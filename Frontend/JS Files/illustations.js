function drawCircle(x, y, radius) {}
function drawRectangle(ctx,x, y, width, height) {
     ctx.save();

    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, width, height);

    ctx.restore();


}
function drawSquare(ctx, x, y, size) {
    drawRectangle(ctx, x, y, size, size);
}
function drawLine(x1, y1, x2, y2) {}
function drawText(text, x, y) {}

function drawSquareLabels(ctx, x, y, size, sideLength) {
    const label = `${sideLength} cm`;
    const gap = 24;

    ctx.save();
    ctx.font = "18px Arial";
    ctx.fillStyle = "#172033";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    // Top and bottom
    ctx.fillText(label, x + size / 2, y - gap);
    ctx.fillText(label, x + size / 2, y + size + gap);

    // Left and right
    ctx.textAlign = "right";
    ctx.fillText(label, x - gap, y + size / 2);

    ctx.textAlign = "left";
    ctx.fillText(label, x + size + gap, y + size / 2);

    ctx.restore();
}