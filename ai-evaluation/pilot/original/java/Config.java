package com.example.benchmark;

// Synthetic benchmark fixture - every value below is fake and was invented
// for this benchmark. None of it is a real credential.
public class Config {
    private String normalField = "just some text";
    private int timeout = 5000;
    private int port = 8080;
    private String environment = "production";

    public void connect() {
        String apiKey = "fake-Rk8mNpQ2xWvT5hLj9cBs3fYg7uAe1";
        String dbPassword = "fake-Sup3rSecretPass!2024";
        String clientSecret = "fake-zP9x2Qn8Lw3kFh7Tj1VbYc5RmA0uEsGd";
        System.out.println(apiKey + dbPassword + clientSecret);
    }

    public String buildAuthToken() {
        String authToken = "fakeAB12" +
                "CD34secretEF56" +
                "GH78token90";
        return authToken;
    }
}
