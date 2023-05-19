using CrawlProject.Models.Domain;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Newtonsoft.Json.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;
using InfluxDB.Client;
using InfluxDB.Client.Api.Domain;
using InfluxDB.Client.Core;
using InfluxDB.Client.Writes;

namespace CrawlProject.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class AuroraController : ControllerBase
    {
        private readonly HttpClient _httpClient;
        private readonly AuroraVisionCredential _auroraVisionCredential;
        private readonly InfluxDBClient _influxDBClient;

        public AuroraController(HttpClient httpClient, AuroraVisionCredential auroraVisionCredential, InfluxDBClient influxDBClient)
        {
            _httpClient = httpClient;
            _auroraVisionCredential = auroraVisionCredential;
            _influxDBClient = influxDBClient;
            _httpClient.DefaultRequestHeaders.Add("X-AuroraVision-ApiKey", "53176d99-c7fb-41e2-9864-173f959e4623-0c81");
        }

        [HttpGet("authenticate")]
        public async Task<IActionResult> Authentication()
        {
            var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-AuroraVision-ApiKey", _auroraVisionCredential.APIKey);
            var byteArray = Encoding.ASCII.GetBytes($"{_auroraVisionCredential.Username}:{_auroraVisionCredential.Password}");
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Basic", Convert.ToBase64String(byteArray));
            var response = await client.GetAsync("https://api.auroravision.net/api/rest/authenticate");
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                var responseJson = JObject.Parse(content);
                _token = responseJson["result"].ToString();
                return Ok(content);
            }
            else
            {
                return BadRequest(response.ReasonPhrase);
            }
        }

        [HttpGet("data")]
        public async Task<IActionResult> GetAurora()
        {
            if (string.IsNullOrEmpty(_token))
            {
                return BadRequest("Token is missing. Please authenticate first.");
            }

            var client = new HttpClient();
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);
            client.DefaultRequestHeaders.Add("X-AuroraVision-Token", _token);
            DateTime today = DateTime.Now;
            string start = today.ToString("yyyyMMdd");
            DateTime yesterday = DateTime.Now.AddDays(-1);
            string end = yesterday.ToString("yyyyMMdd");
            var url = "https://api.auroravision.net/api/rest/v1/stats/power/timeseries/24505719/Irradiance/average?startDate=" + start + "&endDate=" + end + "&sampleSize=Min5&timeZone=Asia/Singapore";
            var response = await client.GetAsync(url);
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadAsStringAsync();

                // Parse the API result and extract the data you want to insert into InfluxDB
                JObject dataJson = JObject.Parse(result);
                var dataArray = dataJson["result"];

                // Create a new InfluxDB write API instance
                var writeApi = _influxDBClient.GetWriteApi();

                // Insert data into InfluxDB
                foreach (var item in dataArray)
                {
                    var start = item.Value<long>("start");
                    var dtObject = DateTimeOffset.FromUnixTimeSeconds(start).UtcDateTime;
                    var isoTimestamp = dtObject.ToString("yyyy-MM-ddTHH:mm:ssZ");
                                        var value = item.Value<decimal>("value");

                    // Create a new InfluxDB point
                    var point = PointData.Measurement("auroraVision")
                        .Tag("tags", 24505719)
                        .Timestamp(DateTime.Parse(isoTimestamp, null, System.Globalization.DateTimeStyles.RoundtripKind))
                        .Field("Irradiance_Min5Avg", value)
                        .Build();

                    // Write the point to InfluxDB
                    writeApi.WritePoint("e5e536bd1a214e56", "47008c0dbbd1ecc5", point);
                }

                // Flush the writes to InfluxDB
                writeApi.Flush();

                return Ok(result);
            }
            else
            {
                return BadRequest(response?.ReasonPhrase);
            }
        }
    }
}

