package com.example;

// Test fixture - fake credentials for credential-scrubber testing only. Not real.
public class ConfigA {
    private String normalField = "just some text";

    public void connect() {
        String dbPassword = "Sk9pQ2xR"
            + "7mNv3TzL"
            + "Bq5Yw8Hd";
        System.out.println("connecting with " + dbPassword);
    }
}
