const socket = io();

const MAX_SAMPLES = 2500;

let totalPeakCount = 0;

const CHART_UPDATE_INTERVAL = 50;
let lastChartUpdate = 0;

let isRecording = false;
let isLoadingStoredData = false;
let isStoredReplay = false;

/*
 * Live timeline state.
 *
 * When true, the timeline follows the newest ECG data.
 * When false, the user has manually moved backward.
 */
let isLiveFollowing = true;

let storedEnd = 0;
let liveEnd = 0;


// --------------------------------------------------
// ECG scrollbar / timeline
// --------------------------------------------------

const ecgScroll =
document.getElementById("ecgScroll");

const timelineStart =
document.getElementById("timelineStart");

const timelinePosition =
document.getElementById("timelinePosition");

const timelineEnd =
document.getElementById("timelineEnd");


// --------------------------------------------------
// Timeline helpers
// --------------------------------------------------

function updateTimelineLabels(start, end, isLive = false) {

    if (timelineStart) {
        timelineStart.textContent =
        Number(start).toLocaleString();
    }

    if (timelineEnd) {
        timelineEnd.textContent =
        Number(end).toLocaleString();
    }

    if (timelinePosition) {

        if (isLive) {
            timelinePosition.textContent = "LIVE";
        }

        else {
            timelinePosition.textContent =
            `${Number(start).toLocaleString()} – ${Number(end).toLocaleString()}`;
        }

    }

}


// --------------------------------------------------
// Set chart window
// --------------------------------------------------

function setChartWindow(start, end) {

    [
        rawChart,
        filteredChart,
        squaredChart

    ].forEach(function(chart) {

        chart.options.scales.x.min = start;
        chart.options.scales.x.max = end;

    });

}


// --------------------------------------------------
// Create chart
// --------------------------------------------------

function createChart(canvasId, label) {

    const canvas =
    document.getElementById(canvasId);

    if (!canvas) {

        console.error(
            "Canvas not found:",
            canvasId
        );

        return null;

    }

    const ctx =
    canvas.getContext("2d");

    return new Chart(
        ctx,
        {

            type: "line",

            data: {

                datasets: [{

                    label: label,

                    data: [],

                    borderWidth: 2,

                    pointRadius: 0,

                    tension: 0

                }]

            },

            options: {

                animation: false,

                responsive: true,

                maintainAspectRatio: false,

                scales: {

                    x: {
                        type: "linear"
                    }

                }

            }

        }
    );

}


// --------------------------------------------------
// Create charts
// --------------------------------------------------

const rawChart =
createChart(
    "rawChart",
    "Raw ECG"
);

const filteredChart =
createChart(
    "filteredChart",
    "Filtered ECG"
);


// --------------------------------------------------
// Squared / QRS chart
// --------------------------------------------------

const squaredCanvas =
document.getElementById(
    "squaredChart"
);

const squaredCtx =
squaredCanvas.getContext("2d");

const squaredChart =
new Chart(
    squaredCtx,
    {

        type: "line",

        data: {

            datasets: [

                {

                    label:
                    "Squared Signal",

                    data: [],

                    borderWidth: 2,

                    pointRadius: 0,

                    tension: 0

                },

                {

                    label:
                    "R-peaks",

                    data: [],

                    showLine: false,

                    pointRadius: 5,

                    pointBackgroundColor:
                    "red",

                    pointBorderColor:
                    "red"

                }

            ]

        },

        options: {

            animation: false,

            responsive: true,

            maintainAspectRatio: false,

            scales: {

                x: {
                    type: "linear"
                }

            }

        }

    }
);


// --------------------------------------------------
// Chart workspace selector
// --------------------------------------------------

const chartByName = {

    raw: rawChart,

    filtered:
    filteredChart,

    squared:
    squaredChart

};

const chartWidgets =
document.querySelectorAll(
    ".chart-widget"
);

const chartPanels =
document.querySelectorAll(
    ".chart-panel"
);


chartWidgets.forEach(
    function(widget) {

        widget.addEventListener(
            "click",
            function() {

                const selectedChart =
                widget.dataset.chartTarget;


                chartWidgets.forEach(
                    function(button) {

                        button.classList.toggle(
                            "active",
                            button === widget
                        );

                    }
                );


                chartPanels.forEach(
                    function(panel) {

                        panel.classList.toggle(
                            "active",
                            panel.dataset.chartPanel ===
                            selectedChart
                        );

                    }
                );


                const chart =
                chartByName[
                    selectedChart
                ];


                if (chart) {

                    chart.resize();

                    chart.update("none");

                }

            }
        );

    }
);


// --------------------------------------------------
// Connection
// --------------------------------------------------

socket.on(
    "connect",
    function() {

        console.log(
            "Socket.IO connected"
        );


        document.getElementById(
            "statusText"
        ).textContent =
        "CONNECTED";


    document.getElementById(
        "statusDot"
    ).style.background =
    "#22c55e";

    }
);


socket.on(
    "disconnect",
    function() {

        console.log(
            "Socket.IO disconnected"
        );


        document.getElementById(
            "statusText"
        ).textContent =
        "DISCONNECTED";


    document.getElementById(
        "statusDot"
    ).style.background =
    "#ef4444";

    }
);


// ==================================================
// CLEAR ALL CHART DATA
// ==================================================

function clearCharts() {

    rawChart.data.datasets[0].data =
    [];

    filteredChart.data.datasets[0].data =
    [];

    squaredChart.data.datasets[0].data =
    [];

    squaredChart.data.datasets[1].data =
    [];


    totalPeakCount = 0;

    storedEnd = 0;

    liveEnd = 0;

    lastChartUpdate = 0;

    isLiveFollowing = true;


    document.getElementById(
        "peakCount"
    ).textContent =
    "0";


    document.getElementById(
        "heartRate"
    ).textContent =
    "--";


    setChartWindow(
        0,
        MAX_SAMPLES
    );


    [
        rawChart,
        filteredChart,
        squaredChart

    ].forEach(
        function(chart) {

            chart.update("none");

        }
    );


    // Reset scrollbar

    if (ecgScroll) {

        ecgScroll.min = 0;

        ecgScroll.max = 0;

        ecgScroll.value = 0;

        ecgScroll.disabled = true;

    }


    updateTimelineLabels(
        0,
        0,
        false
    );

}


// ==================================================
// ECG DATA
// ==================================================

function handleECGData(data) {

    const x =
    data.index;


    // Keep track of latest live sample.

    if (!isStoredReplay) {

        liveEnd = x;

    }


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

            x:
            data.peak_index,

            y:
            data.peak_value

        });


        totalPeakCount++;


        document.getElementById(
            "peakCount"
        ).textContent =
        totalPeakCount;

    }


    // ----------------------------------------------
    // BPM
    // ----------------------------------------------

    if (
        data.bpm !== null &&
        data.bpm !== undefined
    ) {

        document.getElementById(
            "heartRate"
        ).textContent =
        Number(data.bpm).toFixed(1);

    }


    // ----------------------------------------------
    // Rhythm status
    // ----------------------------------------------

    if (data.status) {

        const rhythmStatus =
        document.getElementById(
            "rhythmStatus"
        );


        const displayedStatus =
        data.status === "NORMAL"
        ? "NORMAL"
        : "ALERT: " + data.status;


        rhythmStatus.textContent =
        displayedStatus;


        rhythmStatus.classList.remove(
            "normal",
            "warning",
            "critical"
        );


        if (
            data.status ===
            "NORMAL"
        ) {

            rhythmStatus.classList.add(
                "normal"
            );

        }

        else if (
            data.status ===
            "IRREGULAR"
        ) {

            rhythmStatus.classList.add(
                "warning"
            );

        }

        else if (
            data.status ===
            "TACHYCARDIA" ||

            data.status ===
            "BRADYCARDIA"
        ) {

            rhythmStatus.classList.add(
                "critical"
            );

        }


        document
        .querySelectorAll(
            ".graph-status"
        )
        .forEach(
            function(status) {

                status.textContent =
                displayedStatus;


                status.classList.toggle(
                    "normal",
                    data.status ===
                    "NORMAL"
                );


                status.classList.toggle(
                    "critical",
                    data.status !==
                    "NORMAL"
                );

            }
        );

    }

    // ==================================================
    // CHART WINDOW
    // ==================================================

    const now =
    performance.now();


    if (
        now - lastChartUpdate >=
        CHART_UPDATE_INTERVAL
    ) {

        lastChartUpdate = now;


        // ------------------------------------------
        // LIVE STREAM
        // ------------------------------------------

        if (!isStoredReplay) {

            const oldestSample =
            Math.max(
                0,
                x - MAX_SAMPLES + 1
            );


            rawChart.data.datasets[0].data =
            rawChart.data.datasets[0].data.filter(
                point =>
                point.x >= oldestSample
            );


            filteredChart.data.datasets[0].data =
            filteredChart.data.datasets[0].data.filter(
                point =>
                point.x >= oldestSample
            );


            squaredChart.data.datasets[0].data =
            squaredChart.data.datasets[0].data.filter(
                point =>
                point.x >= oldestSample
            );


            squaredChart.data.datasets[1].data =
            squaredChart.data.datasets[1].data.filter(
                point =>
                point.x >= oldestSample
            );


            /*
             * Auto-follow the live ECG unless the
             * user has manually moved backward.
             */

            if (isLiveFollowing) {

                const start =
                Math.max(
                    0,
                    x - MAX_SAMPLES + 1
                );

                const end =
                x;


                setChartWindow(
                    start,
                    end
                );


                if (ecgScroll) {

                    const maxStart =
                    Math.max(
                        0,
                        x - MAX_SAMPLES + 1
                    );


                    ecgScroll.min = 0;

                    ecgScroll.max =
                    maxStart;

                    ecgScroll.value =
                    maxStart;

                    ecgScroll.disabled =
                    maxStart === 0;


                    updateTimelineLabels(
                        start,
                        end,
                        true
                    );

                }

            }

        }


        rawChart.update("none");

        filteredChart.update("none");

        squaredChart.update("none");

    }

}


// ==================================================
// LIVE ECG STREAM
// ==================================================

socket.on(
    "ecg_data",
    function(data) {

        /*
         * Once stored replay starts, ignore any
         * remaining live ECG packets.
         */

        if (isStoredReplay) {
            return;
        }


        handleECGData(data);

    }
);


// --------------------------------------------------
// Stream finished
// --------------------------------------------------

socket.on(
    "stream_end",
    function() {

        console.log(
            "ECG stream finished."
        );


        document.getElementById(
            "statusText"
        ).textContent =
        "STREAM COMPLETE";


            document.getElementById(
                "statusDot"
            ).style.background =
            "#9ca3af";

    }
);


socket.on(
    "stream_error",
    function(data) {

        console.error(
            "ECG stream error:",
            data.message
        );


        document.getElementById(
            "statusText"
        ).textContent =
        data.message;


        document.getElementById(
            "statusDot"
        ).style.background =
        "#ef4444";

    }
);


// ==================================================
// RECORDING CONTROLS
// ==================================================

const recordButton =
document.getElementById(
    "recordButton"
);

const loadButton =
document.getElementById(
    "loadButton"
);

const recordingStatus =
document.getElementById(
    "recordingStatus"
);


recordButton.addEventListener(
    "click",
    function() {

        if (isRecording) {

            socket.emit(
                "stop_recording"
            );

        }

    }
);


loadButton.addEventListener(
    "click",
    function() {

        if (isLoadingStoredData) {
            return;
        }


        socket.emit(
            "load_stored_data"
        );

    }
);


socket.on(
    "recording_status",
    function(data) {

        isRecording =
        data.recording;


        if (isRecording) {

            recordButton.textContent =
            "■ STOP RECORDING";


    recordButton.classList.add(
        "recording"
    );


    recordingStatus.textContent =
    "RECORDING";

        }

        else {

            recordButton.textContent =
            "● RECORDING STOPPED";


    recordButton.classList.remove(
        "recording"
    );


    recordingStatus.textContent =
    "RECORDING STOPPED";

        }

    }
);


// ==================================================
// STORED DATA START
// ==================================================

socket.on(
    "stored_data_start",
    function() {

        console.log(
            "Starting stored ECG replay."
        );


        /*
         * Prevent incoming live packets from being
         * added to the stored recording.
         */

        isStoredReplay = true;

        isLoadingStoredData = true;

        isLiveFollowing = false;


        /*
         * Completely remove the current live ECG.
         */

        clearCharts();


        /*
         * clearCharts resets the scrollbar and
         * data, so restore replay mode afterward.
         */

        isStoredReplay = true;

        isLiveFollowing = false;


        loadButton.disabled = true;

        loadButton.textContent =
        "LOADING STORED DATA...";


    recordingStatus.textContent =
    "LOADING STORED ECG";

    }
);


// ==================================================
// STORED DATA BATCH
// ==================================================

socket.on(
    "stored_ecg_batch",
    function(data) {

        data.samples.forEach(
            function(sample) {

                storedEnd =
                sample.index;


                handleECGData(
                    sample
                );

            }
        );

    }
);


// ==================================================
// STORED DATA FINISHED
// ==================================================

socket.on(
    "stored_data_end",
    function() {

        console.log(
            "Stored ECG replay ready."
        );


        isLoadingStoredData = false;

        isStoredReplay = true;

        isLiveFollowing = false;


        loadButton.disabled = false;

        loadButton.textContent =
        "REPLAY STORED DATA";


    recordingStatus.textContent =
    "STORED DATA LOADED";


    if (ecgScroll) {

        const maxStart =
        Math.max(
            0,
            storedEnd -
            MAX_SAMPLES +
            1
        );


        ecgScroll.min = 0;

        ecgScroll.max =
        maxStart;

        /*
         * Start at the beginning of the
         * stored recording.
         */

        ecgScroll.value = 0;

        ecgScroll.disabled =
        maxStart === 0;


        const start = 0;

        const end =
        Math.min(
            MAX_SAMPLES - 1,
            storedEnd
        );


        setChartWindow(
            start,
            end
        );


        updateTimelineLabels(
            start,
            end,
            false
        );


        rawChart.update("none");

        filteredChart.update("none");

        squaredChart.update("none");

    }

    }
);


// ==================================================
// STORED DATA ERROR
// ==================================================

socket.on(
    "stored_data_error",
    function(data) {

        console.error(
            "Stored ECG error:",
            data.message
        );


        isLoadingStoredData = false;

        isStoredReplay = false;

        isLiveFollowing = true;


        loadButton.disabled = false;

        loadButton.textContent =
        "LOAD STORED DATA";


    recordingStatus.textContent =
    data.message;


    if (ecgScroll) {

        ecgScroll.disabled = true;

    }

    }
);


// ==================================================
// ECG TIMELINE
// ==================================================

if (ecgScroll) {

    ecgScroll.addEventListener(
        "input",
        function() {

            const start =
            Number(
                ecgScroll.value
            );


            /*
             * ------------------------------------------------
             * STORED REPLAY
             * ------------------------------------------------
             */

            if (isStoredReplay) {

                const end =
                Math.min(
                    start +
                    MAX_SAMPLES -
                    1,
                    storedEnd
                );


                setChartWindow(
                    start,
                    end
                );


                updateTimelineLabels(
                    start,
                    end,
                    false
                );


                /*
                 * If the user reaches the final position,
                 * keep the slider there. Stored replay
                 * remains manually controlled.
                 */

                rawChart.update("none");

                filteredChart.update("none");

                squaredChart.update("none");

                return;

            }


            /*
             * ------------------------------------------------
             * LIVE RECORDING
             * ------------------------------------------------
             */

            if (liveEnd <= 0) {
                return;
            }


            const maxStart =
            Math.max(
                0,
                liveEnd -
                MAX_SAMPLES +
                1
            );


            /*
             * If the slider is at the far right,
             * resume live-follow mode.
             */

            if (start >= maxStart) {

                isLiveFollowing = true;


                const liveStart =
                maxStart;

                const liveStop =
                liveEnd;


                setChartWindow(
                    liveStart,
                    liveStop
                );


                ecgScroll.value =
                maxStart;


                updateTimelineLabels(
                    liveStart,
                    liveStop,
                    true
                );

            }

            else {

                /*
                 * User dragged backward.
                 * Freeze the graph at that location.
                 */

                isLiveFollowing = false;


                const end =
                Math.min(
                    start +
                    MAX_SAMPLES -
                    1,
                    liveEnd
                );


                setChartWindow(
                    start,
                    end
                );


                updateTimelineLabels(
                    start,
                    end,
                    false
                );

            }


            rawChart.update("none");

            filteredChart.update("none");

            squaredChart.update("none");

        }
    );

}
