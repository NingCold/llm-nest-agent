use std::{net::IpAddr, time::Duration};

use reqwest::{Client, Url, redirect::Policy};

use crate::error::{AiError, Result};

pub(crate) fn model_endpoint(base: &str) -> Result<Url> {
    let url =
        Url::parse(base).map_err(|_| AiError::ConfigError("invalid model endpoint URL".into()))?;
    let host = url
        .host_str()
        .ok_or_else(|| AiError::ConfigError("model endpoint requires a host".into()))?;
    let loopback = host == "localhost"
        || host
            .trim_start_matches('[')
            .trim_end_matches(']')
            .parse::<IpAddr>()
            .is_ok_and(|ip| ip.is_loopback());
    if !(url.scheme() == "https" || url.scheme() == "http" && loopback) {
        return Err(AiError::ConfigError(
            "model endpoint requires HTTPS (HTTP is allowed on loopback)".into(),
        ));
    }
    if !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some()
        || url.fragment().is_some()
    {
        return Err(AiError::ConfigError(
            "model endpoint must be a base URL without credentials, query or fragment".into(),
        ));
    }
    Ok(url)
}

pub(super) fn model_client(base: &str, timeout_ms: Option<u64>) -> Result<Client> {
    let url = model_endpoint(base)?;
    let local_http = url.scheme() == "http";
    let mut builder = Client::builder().redirect(Policy::custom(move |attempt| {
        if !same_origin(&url, attempt.url()) {
            attempt.error("model endpoint redirect changed origin")
        } else if attempt.previous().len() >= 10 {
            attempt.error("too many model endpoint redirects")
        } else {
            attempt.follow()
        }
    }));
    if local_http {
        // Plaintext loopback traffic must not be forwarded to a system proxy.
        builder = builder.no_proxy();
    }
    if let Some(ms) = timeout_ms {
        if ms == 0 {
            return Err(AiError::ConfigError(
                "timeout_ms must be a positive number of milliseconds".into(),
            ));
        }
        builder = builder.timeout(Duration::from_millis(ms));
    }
    Ok(builder.build()?)
}

fn same_origin(base: &Url, next: &Url) -> bool {
    base.origin() == next.origin()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::protocols::{
        anthropic::provider::AnthropicProvider, gemini::provider::GeminiProvider,
        openai::provider::OpenAIProvider, openai_responses::provider::OpenAIResponsesProvider,
    };

    #[test]
    fn only_loopback_can_use_plaintext_in_every_adapter() {
        for (url, valid) in [
            ("https://model.example/v1", true),
            ("http://127.0.0.1:8080/v1", true),
            ("http://localhost/v1", true),
            ("http://[::1]/v1", true),
            ("http://model.example/v1", false),
            ("file:///v1", false),
        ] {
            assert_eq!(
                OpenAIProvider::new("model", url, String::new()).is_ok(),
                valid
            );
            assert_eq!(
                OpenAIResponsesProvider::new("model", url, String::new()).is_ok(),
                valid
            );
            assert_eq!(
                AnthropicProvider::new("model", url, String::new()).is_ok(),
                valid
            );
            assert_eq!(
                GeminiProvider::new("model", url, String::new()).is_ok(),
                valid
            );
        }
    }

    #[test]
    fn redirects_require_the_same_scheme_host_and_port() {
        let base = model_endpoint("https://model.example/v1").unwrap();
        assert!(same_origin(
            &base,
            &Url::parse("https://model.example:443/v2").unwrap()
        ));
        for next in [
            "https://other.example/v1",
            "http://model.example/v1",
            "https://model.example:444/v1",
        ] {
            assert!(!same_origin(&base, &Url::parse(next).unwrap()));
        }
    }

    #[tokio::test]
    async fn model_directory_follows_only_same_origin_redirects() {
        use crate::ai_provider::AiProvider;
        use tokio::{
            io::{AsyncReadExt, AsyncWriteExt},
            net::TcpListener,
        };

        for same in [true, false] {
            let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
            let addr = listener.local_addr().unwrap();
            let destination = if same {
                "/directory".to_owned()
            } else {
                format!("http://localhost:{}/directory", addr.port())
            };
            let server = tokio::spawn(async move {
                let mut request = [0u8; 1024];
                let (mut stream, _) = listener.accept().await.unwrap();
                stream.read(&mut request).await.unwrap();
                stream.write_all(format!("HTTP/1.1 302 Found\r\nLocation: {destination}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n").as_bytes()).await.unwrap();
                drop(stream);
                if same {
                    let (mut stream, _) = listener.accept().await.unwrap();
                    stream.read(&mut request).await.unwrap();
                    stream.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 26\r\nConnection: close\r\n\r\n{\"data\":[{\"id\":\"sample\"}]}").await.unwrap();
                }
            });
            let adapter =
                AnthropicProvider::new("local", &format!("http://{addr}"), String::new()).unwrap();
            let models = adapter.list_models().await;
            if same {
                assert_eq!(models.unwrap()[0].id, "sample");
            } else {
                assert!(matches!(models,Err(AiError::Reqwest(ref e)) if e.is_redirect()));
            }
            server.await.unwrap();
        }
    }
}
