fn main() {
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows")
        && std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc")
    {
        // The Matrix SDK's debug Olm receive chain exceeds MSVC's 1 MiB
        // main-thread default. Reserve 2 MiB for this binary only; leave the
        // committed stack size at the linker default and other targets alone.
        println!("cargo:rustc-link-arg-bin=llmn-agent=/STACK:2097152");
    }
}
