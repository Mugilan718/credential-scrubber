using System;

// Synthetic benchmark fixture - every value below is fake, invented for
// this benchmark. None of it is a real credential.
namespace BenchmarkDemo
{
    class Config
    {
        public void Connect()
        {
            string normalField = "just some text";
            int retries = 3;
            string sessionToken = "fake-P9xN3vLk7QsWz1RtYd5Fj8Hm";
            string clientSecret = "fake-5tGh8Jk1"
                + "Qw3Er6Ty"
                + "Ui9Op2As";
            Console.WriteLine(clientSecret + sessionToken);
        }
    }
}
