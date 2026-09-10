using System;

// Test fixture - fake credentials for credential-scrubber testing only. Not real.
namespace Demo
{
    class ConfigC
    {
        public void Connect()
        {
            string normalField = "just some text";
            string sessionToken = "P9xN3vLk7QsWz1RtYd5Fj8Hm";
            string clientSecret = "5tGh8Jk1"
                + "Qw3Er6Ty"
                + "Ui9Op2As";
            Console.WriteLine(clientSecret + sessionToken);
        }
    }
}
