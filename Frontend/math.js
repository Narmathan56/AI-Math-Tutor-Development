// =========================
// PAGE TOGGLE
// =========================
function openWhiteboard() {
    document.getElementById("chatPage").classList.remove("active");
    document.getElementById("canvasPage").classList.add("active");
}

function openChat() {
    document.getElementById("canvasPage").classList.remove("active");
    document.getElementById("chatPage").classList.add("active");
}



// =========================
// GLOBAL STATE
// =========================
let canvas = null;
let ctx = null;
let drawing = false;

// streaming buffer
let liveText = "";

// =========================
// INIT CANVAS
// =========================
window.addEventListener("DOMContentLoaded", () => {
    canvas = document.getElementById("board");

    if (!canvas) {
        console.error("Canvas not found!");
        return;
    }

    ctx = canvas.getContext("2d");

    canvas.addEventListener("mousedown", startDraw);
    canvas.addEventListener("mousemove", draw);
    canvas.addEventListener("mouseup", stopDraw);
    canvas.addEventListener("mouseleave", stopDraw);
});


function cleanExpression(expr) {
    return String(expr)
        .replace(/\\text\{([^}]*)\}/g, "$1")
        .replace(/\\pm/g, "±")
        .replace(/\\sqrt\{([^}]*)\}/g, "√($1)")
        .replace(/\\/g, "");
}

// =========================
// DRAW FUNCTIONS
// =========================
function startDraw(e) {
    if (!ctx) return;

    drawing = true;
    ctx.beginPath();
    ctx.moveTo(e.offsetX, e.offsetY);
}

function draw(e) {
    if (!drawing || !ctx) return;

    ctx.lineWidth = 2;
    ctx.lineCap = "round";

    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();
}

function stopDraw() {
    drawing = false;
}

// =========================
// CLEAR CANVAS
// =========================
function clearCanvas() {
    if (!ctx || !canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// =========================
// SAFE TEXT CONVERTER
// =========================
function convertToLatex(text) {
    if (text === null || text === undefined) return "";
    text = String(text);

    return text.replace(/([a-zA-Z])(\d+)/g, "$1^{$2}");
}

// =========================
// MATH RENDER
// =========================
function renderMath() {
    renderMathInElement(document.getElementById("replyText"), {
        delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false }
        ]
    });
}

// =========================
// STREAMING RENDER (CHAT + CANVAS SYNC)
// =========================
function updateLiveUI(chunk) {
    const replyText = document.getElementById("replyText");

    liveText += chunk;

    // show chat live
    replyText.innerHTML = convertToLatex(liveText);

    // optional: live canvas update
    if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = "20px Arial";
        ctx.fillText(liveText, 20, 50);
    }
}

// =========================
// MAIN STREAMING CALL
// =========================
async function askTutor() {

    const question = document.getElementById("mathQuestion").value;
    const replyText = document.getElementById("replyText");
    const container = document.getElementById("responseContainer");

    if (!question) return;

    liveText = "";
    replyText.innerHTML = "";
    container.classList.remove("hidden");

    try {
        const response = await fetch("http://127.0.0.1:8000/solve_math_stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // SSE messages are separated by \n\n
            let parts = buffer.split("\n\n");
            buffer = parts.pop();

            for (let part of parts) {

                if (!part.startsWith("data:")) continue;

                const jsonStr = part.replace("data:", "").trim();

                try {
                    const chunk = JSON.parse(jsonStr);

                    // =========================
                    // STREAM TOKEN (TEXT)
                    // =========================
                    if (chunk.type === "token") {

                        liveText += chunk.text;

                        replyText.innerHTML = convertToLatex(liveText);

                        if (ctx) {
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                            ctx.font = "20px Arial";
                            ctx.fillText(liveText, 20, 50);
                        }
                    }

                    // =========================
                    // FINAL RESULT
                    // =========================
                    if (chunk.type === "done") {

    // parse JSON safely
                        let data = null;

                        try {
        data = typeof chunk.full === "string"
            ? JSON.parse(chunk.full)
            : chunk.full;
    } catch (e) {
        console.error("JSON parse failed", e);
        return;
    }

    // extract clean answer
    const answer = data.final_answer;

    // UI display (clean)
    replyText.innerHTML += `<br><b>Final Answer:</b> ${answer}`;

    // canvas display (clean)
 
    drawSolution(data.steps, answer);

    openWhiteboard();
}

                } catch (e) {
                    console.error("Stream parse error:", e, jsonStr);
                }
            }
        }

    } catch (err) {
        console.error(err);
        replyText.innerHTML = "Backend streaming error";
    }
}

function drawStepArrow(x, y) {
    ctx.beginPath();

    // shaft
    ctx.moveTo(x, y);
    ctx.lineTo(x, y + 25);
    ctx.stroke();

    // arrow head
    ctx.beginPath();
    ctx.moveTo(x - 6, y + 18);
    ctx.lineTo(x, y + 25);
    ctx.lineTo(x + 6, y + 18);
    ctx.stroke();
}



    
// =========================
// FINAL CANVAS DRAW
// =========================

function drawSolution(steps, answer) {

    if (!canvas || !ctx) return;

    clearCanvas();

    const START_X = 40;
    const START_Y = 50;

    const FONT_SIZE = 20;
    const LINE_HEIGHT = 30;

    const ARROW_HEIGHT = 45;
    const ARROW_GAP = 15;

    const STEP_GAP = 35;

    const MAX_WIDTH = canvas.width - 80;

    // ---------------------------------
    // FONT
    // ---------------------------------

    ctx.font = `${FONT_SIZE}px Arial`;
    ctx.fillStyle = "black";
    ctx.lineWidth = 2;

    // ---------------------------------
    // WRAP TEXT
    // ---------------------------------

    function wrapText(text, x, y, maxWidth) {

        const words = String(text).split(" ");

        let line = "";
        let currentY = y;

        for (const word of words) {

            const testLine =
                line + (line ? " " : "") + word;

            const width = ctx.measureText(testLine).width;

            if (width > maxWidth && line !== "") {

                ctx.fillText(line, x, currentY);

                line = word;

                currentY += LINE_HEIGHT;

            } else {

                line = testLine;
            }
        }

        if (line) {
            ctx.fillText(line, x, currentY);
        }

        return currentY;
    }

    // ---------------------------------
    // CALCULATE HEIGHT
    // ---------------------------------

    let requiredHeight = START_Y;

    for (const step of (steps || [])) {

        // Prefer expression for mathematical steps
        const text = cleanExpression(
            step.expression ||
            step.text ||
            ""
        );

        const words = text.split(" ");

        let line = "";
        let lines = 1;

        for (const word of words) {

            const testLine =
                line + (line ? " " : "") + word;

            if (
                ctx.measureText(testLine).width >
                MAX_WIDTH
            ) {

                lines++;

                line = word;

            } else {

                line = testLine;
            }
        }

        requiredHeight +=
            (lines * LINE_HEIGHT) +
            STEP_GAP;

        // Arrow space
        if (step !== steps[steps.length - 1]) {

            requiredHeight +=
                ARROW_GAP +
                ARROW_HEIGHT +
                STEP_GAP;
        }
    }

    // Final answer
    requiredHeight += 100;

    // ---------------------------------
    // RESIZE CANVAS
    // ---------------------------------

    canvas.height = Math.max(
        500,
        requiredHeight
    );

    // IMPORTANT:
    // resizing canvas resets context
    ctx = canvas.getContext("2d");

    ctx.font = `${FONT_SIZE}px Arial`;
    ctx.fillStyle = "black";
    ctx.lineWidth = 2;

    // ---------------------------------
    // DRAW ARROW
    // ---------------------------------

    function drawStepArrow(x, y) {

        ctx.beginPath();

        // vertical line
        ctx.moveTo(x, y);

        ctx.lineTo(
            x,
            y + ARROW_HEIGHT - 10
        );

        ctx.stroke();

        // arrow head
        ctx.beginPath();

        ctx.moveTo(
            x - 7,
            y + ARROW_HEIGHT - 18
        );

        ctx.lineTo(
            x,
            y + ARROW_HEIGHT
        );

        ctx.lineTo(
            x + 7,
            y + ARROW_HEIGHT - 18
        );

        ctx.stroke();
    }

    // ---------------------------------
    // DRAW STEPS
    // ---------------------------------

    let y = START_Y;

    for (let i = 0; i < (steps || []).length; i++) {

        const step = steps[i];

        const expression = cleanExpression(
            step.expression ||
            step.text ||
            ""
        );

        // Draw step
        y = wrapText(
            expression,
            START_X,
            y,
            MAX_WIDTH
        );

        // Space after text
        y += STEP_GAP;

        // Arrow
        if (i < steps.length - 1) {

            drawStepArrow(
                START_X + 20,
                y
            );

            y += ARROW_HEIGHT + ARROW_GAP;
        }
    }

    // ---------------------------------
    // FINAL ANSWER
    // ---------------------------------

    y += 20;

    ctx.font = "bold 22px Arial";

    ctx.fillText(
        "Answer:",
        START_X,
        y
    );

    y += 35;

    ctx.font = "22px Arial";

    ctx.fillText(
        String(answer),
        START_X,
        y
    );
}