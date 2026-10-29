//! Exercise the real executable with the desktop's hidden-process startup contract.
use serde_json::{Value, json};
use std::{path::Path, process::Stdio, time::Duration};
use tokio::io::{AsyncBufReadExt, BufReader};

fn command(verb: &str, directory: &Path) -> tokio::process::Command {
    let mut command = tokio::process::Command::new(env!("CARGO_BIN_EXE_llmn-agent"));
    command
        .args([verb])
        .arg(directory)
        .env_remove("API_KEY_CHATECNU")
        .env("LLMN_MANAGED_TEST_KEY", "fixture-only-not-a-real-key")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .kill_on_drop(true);
    #[cfg(windows)]
    command.creation_flags(0x08000000);
    command
}

fn fixture_config(directory: &Path, server: &str) -> toml::Value {
    let path = directory.join("node.toml");
    let mut config: toml::Value = toml::from_str(&std::fs::read_to_string(&path).unwrap()).unwrap();
    config["server"] = server.into();
    config["profile"] = toml::Value::try_from(json!({
        "revision":"1", "persona":"Fixture assistant",
        "selection":{"provider":"fixture","model":"fixture"}, "max_tokens":128
    }))
    .unwrap();
    config["providers"] = toml::Value::try_from(json!({"fixture":{
        "protocol":"openai",
        "api_key":{"env":"LLMN_MANAGED_TEST_KEY"},
        "base_url":format!("{server}/v1"),
        "models":{"fixture":{"model":"fixture","context_window":8192,"max_tokens":1024}}
    }}))
    .unwrap();
    std::fs::write(path, toml::to_string(&config).unwrap()).unwrap();
    config
}

async fn status(directory: &Path) -> Value {
    let output = command("status", directory).output().await.unwrap();
    assert!(output.status.success());
    serde_json::from_slice(&output.stdout).unwrap()
}

#[tokio::test]
async fn hidden_managed_start_acknowledges_before_immediate_status_probes() {
    let fixture = tempfile::tempdir().unwrap();
    let directory = fixture.path().join("node");
    assert!(
        command("init", &directory)
            .output()
            .await
            .unwrap()
            .status
            .success()
    );
    let config = fixture_config(&directory, "http://127.0.0.1:1");
    let profile = serde_json::to_string(&config["profile"]).unwrap();
    {
        let db = rusqlite::Connection::open(directory.join("node.sqlite")).unwrap();
        db.execute(
            "INSERT INTO bindings VALUES('fixture-ai','1','fixture-credential')",
            [],
        )
        .unwrap();
        db.execute("INSERT INTO profiles VALUES('fixture-ai',?1)", [&profile])
            .unwrap();
    }
    for _ in 0..20 {
        let mut child = command("run-managed", &directory).spawn().unwrap();
        let mut lines = BufReader::new(child.stdout.take().unwrap()).lines();
        let line = tokio::time::timeout(Duration::from_secs(5), lines.next_line())
            .await
            .expect("managed startup must acknowledge readiness")
            .unwrap()
            .expect("managed startup exited before readiness");
        let ready: Value = serde_json::from_str(&line).unwrap();
        assert_eq!(ready["type"], "ready");
        for _ in 0..3 {
            // Previously this probe could win the exclusive directory lock and
            // make the newly spawned Agent exit with 'directory already in use'.
            let observed = status(&directory).await;
            assert_eq!(observed["running"], true);
            assert_eq!(observed["instanceId"], ready["instanceId"]);
            assert_eq!(observed["aiIds"], json!(["fixture-ai"]));
            assert!(child.try_wait().unwrap().is_none());
        }
        assert!(
            command("stop", &directory)
                .output()
                .await
                .unwrap()
                .status
                .success()
        );
        assert!(
            tokio::time::timeout(Duration::from_secs(5), child.wait())
                .await
                .unwrap()
                .unwrap()
                .success()
        );
        assert_eq!(status(&directory).await["running"], false);
    }
}

#[tokio::test]
async fn transfer_export_uses_directory_lock_and_preserves_database() {
    let fixture = tempfile::tempdir().unwrap();
    let directory = fixture.path().join("node");
    assert!(
        command("init", &directory)
            .output()
            .await
            .unwrap()
            .status
            .success()
    );
    let config = fixture_config(&directory, "http://127.0.0.1:1");
    let ai = uuid::Uuid::new_v4().to_string();
    let database = directory.join("node.sqlite");
    {
        let db = rusqlite::Connection::open(&database).unwrap();
        db.execute(
            "INSERT INTO profiles VALUES(?1,?2)",
            rusqlite::params![ai, serde_json::to_string(&config["profile"]).unwrap()],
        )
        .unwrap();
    }
    let before = std::fs::read(&database).unwrap();
    let output = fixture.path().join("package.json");
    let lock = std::fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(directory.join("node.lock"))
        .unwrap();
    fs2::FileExt::try_lock_exclusive(&lock).unwrap();
    let failed = command("export-ai", &directory)
        .arg(&ai)
        .arg(&output)
        .output()
        .await
        .unwrap();
    assert!(!failed.status.success());
    assert!(!output.exists());
    drop(lock);
    assert!(
        command("export-ai", &directory)
            .arg(&ai)
            .arg(&output)
            .output()
            .await
            .unwrap()
            .status
            .success()
    );
    assert_eq!(before, std::fs::read(database).unwrap());
    assert!(
        !command("export-ai", &directory)
            .arg(&ai)
            .arg(&output)
            .output()
            .await
            .unwrap()
            .status
            .success()
    );
    let package: Value = serde_json::from_slice(&std::fs::read(output).unwrap()).unwrap();
    assert_eq!(package["version"], 1);
    assert_eq!(package["aiId"], ai);
}

#[tokio::test]
async fn managed_crypto_restart_processes_successful_sdk_responses() {
    use std::sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    };
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let crypto_requests = Arc::new(AtomicUsize::new(0));
    let key_queries = Arc::new(AtomicUsize::new(0));
    let queried = key_queries.clone();
    let observed = crypto_requests.clone();
    let server = tokio::spawn(async move {
        loop {
            let (mut stream, _) = listener.accept().await.unwrap();
            let observed = observed.clone();
            let queried = queried.clone();
            tokio::spawn(async move {
                let mut request = Vec::new();
                loop {
                    let mut buffer = [0; 4096];
                    let count = stream.read(&mut buffer).await.unwrap();
                    if count == 0 {
                        return;
                    }
                    request.extend_from_slice(&buffer[..count]);
                    if let Some(end) = request.windows(4).position(|bytes| bytes == b"\r\n\r\n") {
                        let headers = String::from_utf8_lossy(&request[..end]);
                        let length = headers
                            .lines()
                            .find_map(|line| {
                                let (name, value) = line.split_once(':')?;
                                name.eq_ignore_ascii_case("content-length")
                                    .then(|| value.trim().parse::<usize>().unwrap())
                            })
                            .unwrap_or(0);
                        if request.len() >= end + 4 + length {
                            break;
                        }
                    }
                }
                let headers_end = request
                    .windows(4)
                    .position(|bytes| bytes == b"\r\n\r\n")
                    .unwrap();
                let headers = String::from_utf8_lossy(&request[..headers_end]);
                let path = headers.lines().next().unwrap();
                let (status, body) = if path.contains("/changes") {
                    ("200 OK", json!({"cursor":"0","hasMore":false,"changes":[]}))
                } else if path.contains("/crypto/devices") {
                    ("200 OK", json!({}))
                } else if path.contains("/crypto/requests") {
                    let request: Value =
                        serde_json::from_slice(&request[headers_end + 4..]).unwrap();
                    if request["kind"] == "keysQuery" {
                        queried.fetch_add(1, Ordering::SeqCst);
                    }
                    let response = match request["kind"].as_str().unwrap() {
                        "keysQuery" => {
                            json!({"device_keys":{},"master_keys":{},"self_signing_keys":{},"user_signing_keys":{},"failures":{}})
                        }
                        "keysUpload" => json!({"one_time_key_counts":{"signed_curve25519":50}}),
                        _ => json!({}),
                    };
                    ("200 OK", response)
                } else if path.contains("/crypto/sync") {
                    (
                        "200 OK",
                        json!({"next_batch":"0","to_device":{"events":[]},"device_lists":{"changed":[],"left":[]},"device_one_time_keys_count":{"signed_curve25519":50},"device_unused_fallback_key_types":[]}),
                    )
                } else if path.contains("/crypto/resources") {
                    // Material fetch happens only after successful SDK key
                    // acknowledgements and processing the sync response.
                    observed.fetch_add(1, Ordering::SeqCst);
                    ("200 OK", json!({"items":[]}))
                } else if path.contains("/crypto/conversations") {
                    ("200 OK", json!({"conversations":[]}))
                } else {
                    ("503 Unavailable", json!({}))
                };
                let body = body.to_string();
                let response = format!(
                    "HTTP/1.1 {status}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
                    body.len()
                );
                let _ = stream.write_all(response.as_bytes()).await;
            });
        }
    });
    let fixture = tempfile::tempdir().unwrap();
    let directory = fixture.path().join("node");
    assert!(
        command("init", &directory)
            .output()
            .await
            .unwrap()
            .status
            .success()
    );
    let config = fixture_config(&directory, &format!("http://{address}"));
    let ai = uuid::Uuid::new_v4().to_string();
    let device_id = uuid::Uuid::new_v4().to_string();
    let key = [42_u8; 32];
    {
        let device =
            llmn_crypto::Device::open(&directory.join("crypto").join(&ai), &ai, &device_id, &key)
                .await
                .unwrap();
        assert_eq!(device.machine().device_id().as_str(), device_id);
        let peer = llmn_crypto::ruma::UserId::parse("@peer:llmn").unwrap();
        device
            .machine()
            .update_tracked_users([peer.as_ref()])
            .await
            .unwrap();
    }
    {
        let db = rusqlite::Connection::open(directory.join("node.sqlite")).unwrap();
        db.execute(
            "INSERT INTO bindings VALUES(?1,'1','fixture-credential')",
            [&ai],
        )
        .unwrap();
        db.execute(
            "INSERT INTO profiles VALUES(?1,?2)",
            rusqlite::params![ai, serde_json::to_string(&config["profile"]).unwrap()],
        )
        .unwrap();
        db.execute_batch("CREATE TABLE crypto_devices(ai TEXT PRIMARY KEY,device TEXT NOT NULL,local_key BLOB NOT NULL,cursor TEXT NOT NULL DEFAULT '0',ready INTEGER NOT NULL DEFAULT 0);").unwrap();
        db.execute(
            "INSERT INTO crypto_devices(ai,device,local_key) VALUES(?1,?2,?3)",
            rusqlite::params![ai, device_id, key.as_slice()],
        )
        .unwrap();
    }
    let mut child = command("run-managed", &directory)
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let mut lines = BufReader::new(child.stdout.take().unwrap()).lines();
    let ready = tokio::time::timeout(Duration::from_secs(5), lines.next_line())
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    assert_eq!(
        serde_json::from_str::<Value>(&ready).unwrap()["type"],
        "ready"
    );
    tokio::time::timeout(Duration::from_secs(10), async {
        while crypto_requests.load(Ordering::SeqCst) == 0 {
            if let Some(exit) = child.try_wait().unwrap() {
                let mut stderr = String::new();
                child
                    .stderr
                    .take()
                    .unwrap()
                    .read_to_string(&mut stderr)
                    .await
                    .unwrap();
                panic!("managed crypto startup exited {exit}: {stderr}");
            }
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .expect("existing SDK identity must reopen, acknowledge key responses and process cloud sync");
    assert!(child.try_wait().unwrap().is_none());
    assert!(
        key_queries.load(Ordering::SeqCst) > 0,
        "the SDK key-query response must be acknowledged before sync"
    );
    assert!(
        command("stop", &directory)
            .output()
            .await
            .unwrap()
            .status
            .success()
    );
    assert!(
        tokio::time::timeout(Duration::from_secs(5), child.wait())
            .await
            .unwrap()
            .unwrap()
            .success()
    );
    server.abort();
}
