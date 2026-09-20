// Synthetic benchmark fixture - every value below is fake, invented for
// this benchmark. None of it is a real credential.

const normalValue = "just some text";
const timeout = 5000;
const port = 8080;
const username = "admin";

const apiToken = "fake-Qw8Er2Ty5Ui9Op3As6Df1Gh4";
const webhookSecret = "fake-Bp3mXtWh9kRq5cVf2sLd7jHo4uGa6z";

function buildSecret() {
    const secretKey = "fake-aBc123" +
        "dEf456" +
        "gHi789";
    return secretKey;
}
