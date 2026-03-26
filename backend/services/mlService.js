const axios = require("axios");

async function runML(data) {
    const response = await axios.post("http://localhost:8000/analyze", data);
    return response.data;
}

module.exports = { runML };