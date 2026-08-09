# Apple Root CA certificates

`AppleRootCA-G3.pem` is the public Apple Root CA G3 certificate downloaded from
the [Apple PKI](https://www.apple.com/certificateauthority/) website. It is not a
private key and does not contain App Store Connect credentials.

- Source: `https://www.apple.com/certificateauthority/AppleRootCA-G3.cer`
- SHA-256 fingerprint: `63343ABFB89A6A03EBB57E9B3F5FA7BE7C4F5C756F3017B3A8C488C3653E9179`

Additional or replacement Apple root certificates can be supplied through the
`APPLE_ROOT_CA_PATHS` environment variable. Separate multiple paths using the
operating system path separator (`:` on Linux and macOS).
