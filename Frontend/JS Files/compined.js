
function renderVisual(instructions) {
    instructions.forEach(instruction => {

        switch (instruction.type) {

            case "circle":
                drawCircle(
                    instruction.x,
                    instruction.y,
                    instruction.radius
                );
                break;

            case "rectangle":
                drawRectangle(
                    instruction.x,
                    instruction.y,
                    instruction.width,
                    instruction.height
                );
                break;
            case "square":
                drawSquare(instruction.x, instruction.y, instruction.size);
                break;
            case "line":
                drawLine(
                    instruction.x1,
                    instruction.y1,
                    instruction.x2,
                    instruction.y2
                );
                break;    
        }
    });
}