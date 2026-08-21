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

    if (!ctx || !canvas) return;

    clearCanvas();

    const START_X = 30;
    const START_Y = 40;
    const MAX_WIDTH = canvas.width - 60;

    const FONT_SIZE = 18;
    const LINE_HEIGHT = 28;
    const ARROW_GAP = 12;
    const ARROW_HEIGHT = 25;
    const STEP_GAP = 15;

    ctx.font = `${FONT_SIZE}px Arial`;
    ctx.fillStyle = "black";
    ctx.lineWidth = 2;

    // =========================
    // TEXT WRAPPING
    // =========================
    function wrapText(text, x, y, maxWidth) {

        const words = String(text).split(" ");
        let line = "";
        let currentY = y;

        for (let i = 0; i < words.length; i++) {

            const testLine =
                line + (line ? " " : "") + words[i];

            const width = ctx.measureText(testLine).width;

            if (width > maxWidth && line !== "") {

                ctx.fillText(line, x, currentY);

                line = words[i];
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

    // =========================
    // ARROW
    // =========================
    function drawStepArrow(x, y) {

        ctx.beginPath();

        // vertical line
        ctx.moveTo(x, y);
        ctx.lineTo(x, y + ARROW_HEIGHT - 6);
        ctx.stroke();

        // arrow head
        ctx.beginPath();

        ctx.moveTo(
            x - 6,
            y + ARROW_HEIGHT - 10
        );

        ctx.lineTo(
            x,
            y + ARROW_HEIGHT
        );

        ctx.lineTo(
            x + 6,
            y + ARROW_HEIGHT - 10
        );

        ctx.stroke();
    }

    // =========================
    // DRAW STEPS
    // =========================

    let y = START_Y;

    for (let i = 0; i < (steps || []).length; i++) {

        const step = steps[i];

       const expression = cleanExpression(
        step.expression ||
        step.text ||
        ""
    );

        // Don't overflow canvas
        if (y > canvas.height - 80) {
            break;
        }

        // Draw expression
        y = wrapText(
            expression,
            START_X,
            y,
            MAX_WIDTH
        );

        // =========================
        // ARROW TO NEXT STEP
        // =========================

        if (i < steps.length - 1) {

            y += ARROW_GAP;

            drawStepArrow(
                START_X + 15,
                y
            );

            y += ARROW_HEIGHT + STEP_GAP;
        }
    }

    // =========================
    // FINAL ANSWER
    // =========================

    if (y < canvas.height - 50) {

        y += 10;

        ctx.font = "bold 18px Arial";

        ctx.fillText(
            "Answer:",
            START_X,
            y
        );

        y += LINE_HEIGHT;

        ctx.font = "18px Arial";

        ctx.fillText(
            String(answer),
            START_X,
            y
        );
    }
}