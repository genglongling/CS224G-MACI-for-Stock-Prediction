async function fetchStockData() {
  let symbols = document.getElementById("stockSymbols").value;
  let resultDiv = document.getElementById("result");

  if (!symbols) {
    resultDiv.innerHTML = "<p style='color: red;'>Please enter stock symbols.</p>";
    return;
  }

  resultDiv.innerHTML = "<p>Fetching data...</p>";

  try {
    let response = await fetch(`/investment_research?question=${encodeURIComponent(symbols)}`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    let data = await response.text(); // Get raw response as text
    resultDiv.innerHTML = `<pre>${data}</pre>`; // Display full raw response

  } catch (error) {
    resultDiv.innerHTML = `<p style='color: red;'>Failed to fetch stock data: ${error.message}</p>`;
  }
}

function generateAndExportAgent() {
    alert("Agent Generated! Redirecting to Stock Prediction...");
    window.location.href = "index.html";
}
