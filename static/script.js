const socket = io();

const MAX_SAMPLES = 2500;
let totalPeakCount = 0;
// Update charts at ~20 FPS instead of every sample
const CHART_UPDATE_INTERVAL = 50;
let lastChartUpdate = 0;


// --------------------------------------------------
// Create chart
// --------------------------------------------------

function createChart(canvasId, label) {

    const ctx = document
    .getElementById(canvasId)
    .getContext("2d");

    return new Chart(ctx, {

        type: "line",

        data: {
            datasets: [
                {
                    label: label,
                    data: [],
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },

        options: {
            animation: false,
            responsive: true,

            scales: {
                x: {
                    type: "linear"
                }
            }
        }
    });
}


// --------------------------------------------------
// Create three charts
// --------------------------------------------------

const rawChart =
createChart("rawChart", "Raw ECG");

const filteredChart =
createChart("filteredChart", "Filtered ECG");


// Squared chart needs two datasets

const squaredCtx = document
.getElementById("squaredChart")
.getContext("2d");

const squaredChart = new Chart(squaredCtx, {

    type: "line",

    data: {
        datasets: [

            {
                label: "Squared Signal",
                data: [],
                borderWidth: 2,
                pointRadius: 0,
                tension: 0
            },

            {
                label: "R-peaks",
                data: [],
                showLine: false,
                pointRadius: 5,
                pointBackgroundColor: "red",
                pointBorderColor: "red"
            }

        ]
    },

    options: {
        animation: false,
        responsive: true,

        scales: {
            x: {
                type: "linear"
            }
        }
    }
});


// --------------------------------------------------
// Connection
// --------------------------------------------------

socket.on("connect", () => {

    console.log("Connected");

    document.getElementById("statusText")
    .textContent = "CONNECTED";

    document.getElementById("statusDot")
    .style.background = "#22c55e";

});


socket.on("disconnect", () => {

    document.getElementById("statusText")
    .textContent = "DISCONNECTED";

    document.getElementById("statusDot")
    .style.background = "#ef4444";

});


// --------------------------------------------------
// Incoming ECG data
// --------------------------------------------------

socket.on("ecg_data", function(data) {

    const x = data.index;


    // ----------------------------------------------
    // Raw ECG
    // ----------------------------------------------

    rawChart.data.datasets[0].data.push({

        x: x,
        y: data.raw

    });


    // ----------------------------------------------
    // Filtered ECG
    // ----------------------------------------------

    filteredChart.data.datasets[0].data.push({

        x: x,
        y: data.filtered

    });


    // ----------------------------------------------
    // Squared signal
    // ----------------------------------------------

    squaredChart.data.datasets[0].data.push({

        x: x,
        y: data.squared

    });


    // ----------------------------------------------
    // R-peak
    // ----------------------------------------------

    if (data.peak) {

        squaredChart.data.datasets[1].data.push({

            x: data.peak_index,
            y: data.peak_value

        });

        totalPeakCount++;

        document.getElementById("peakCount")
        .textContent = totalPeakCount;
    }


    // ----------------------------------------------
    // BPM
    // ----------------------------------------------

    if (data.bpm !== null) {

        document.getElementById("heartRate")
        .textContent =
        data.bpm.toFixed(1) + " BPM";

    }
    // ----------------------------------------------
    // Rhythm status + alert
    // ----------------------------------------------

    if (data.status) {

        const rhythmStatus =
        document.getElementById("rhythmStatus");

        const alertMessage =
        document.getElementById("alertMessage");

        if (rhythmStatus) {

            rhythmStatus.textContent = data.status;

            // Remove previous states
            rhythmStatus.classList.remove(
                "normal",
                "warning",
                "critical"
            );

            if (data.status === "NORMAL") {

                rhythmStatus.classList.add("normal");

            }

            else if (
                data.status === "TACHYCARDIA" ||
                data.status === "BRADYCARDIA"
            ) {

                rhythmStatus.classList.add("critical");

            }
        }


        // ------------------------------------------
        // Alert
        // ------------------------------------------

        if (alertMessage) {

            if (data.alert === true) {

                alertMessage.textContent =
                "⚠ RHYTHM ALERT: " + data.status;

                alertMessage.classList.add("active");

            }

            else {

                alertMessage.textContent = "";

                alertMessage.classList.remove("active");

            }
        }
    }

    // ----------------------------------------------
    // Update charts periodically
    // ----------------------------------------------

    const now = performance.now();

    if (now - lastChartUpdate >= CHART_UPDATE_INTERVAL) {

        lastChartUpdate = now;

        const oldestSample =
        x - MAX_SAMPLES;


        // ------------------------------------------
        // Rolling window
        // ------------------------------------------

        rawChart.data.datasets[0].data =
        rawChart.data.datasets[0].data.filter(
            point => point.x >= oldestSample
        );


        filteredChart.data.datasets[0].data =
        filteredChart.data.datasets[0].data.filter(
            point => point.x >= oldestSample
        );


        squaredChart.data.datasets[0].data =
        squaredChart.data.datasets[0].data.filter(
            point => point.x >= oldestSample
        );


        squaredChart.data.datasets[1].data =
        squaredChart.data.datasets[1].data.filter(
            point => point.x >= oldestSample
        );


        // ------------------------------------------
        // Move x-axis
        // ------------------------------------------

        const charts = [
            rawChart,
            filteredChart,
            squaredChart
        ];


        charts.forEach(chart => {

            chart.options.scales.x.min =
            Math.max(0, oldestSample);

            chart.options.scales.x.max =
            Math.max(MAX_SAMPLES, x);

        });


        // ------------------------------------------
        // Update charts
        // ------------------------------------------

        rawChart.update("none");

        filteredChart.update("none");

        squaredChart.update("none");

    }

});

// --------------------------------------------------
// Stream finished
// --------------------------------------------------

socket.on("stream_end", function() {

    console.log("ECG stream finished.");

    document.getElementById("statusText")
    .textContent = "STREAM COMPLETE";

    document.getElementById("statusDot")
    .style.background = "#9ca3af";

});

