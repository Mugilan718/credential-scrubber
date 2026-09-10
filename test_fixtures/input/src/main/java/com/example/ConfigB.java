package com.example;

// Test fixture - fake credentials for credential-scrubber testing only. Not real.
public class ConfigB {
    public String buildAuthToken() {
        String authToken = "aBcD1234" +
                "eFgH5678" +
                "iJkL9012";
        return authToken;
    }
}
