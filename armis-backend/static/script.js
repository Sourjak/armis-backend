const apiUrl = "/data";
let tempData = [];
let humData = [];
let labels = [];

const tempCtx = document.getElementById("tempChart").getContext("2d");
const humCtx = document.getElementById("humChart").getContext("2d");

const tempChart = new Chart(tempCtx, {
  type: "line",
  data: { labels, datasets: [{ label: "Temperature", data: tempData, borderColor: "red" }] },
});

const humChart = new Chart(humCtx, {
  type: "line",
  data: { labels, datasets: [{ label: "Humidity", data: humData, borderColor: "blue" }] },
});

async function fetchData() {
  const res = await fetch(apiUrl);
  const data = await res.json();

  document.getElementById("temp").innerText = data.temperature || "--";
  document.getElementById("humidity").innerText = data.humidity || "--";
  document.getElementById("rain").innerText = data.rain || "--";
  document.getElementById("soil").innerText = data.soil || "--";
  document.getElementById("gps").innerText = `${data.gps_lat || "--"}, ${data.gps_lon || "--"}`;

  if (data.temperature && data.humidity) {
    labels.push(new Date().toLocaleTimeString());
    tempData.push(data.temperature);
    humData.push(data.humidity);

    if (labels.length > 10) {
      labels.shift();
      tempData.shift();
      humData.shift();
    }

    tempChart.update();
    humChart.update();
  }
}

setInterval(fetchData, 3000);
