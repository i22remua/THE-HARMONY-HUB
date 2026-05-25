import AppKit

let arguments = CommandLine.arguments

guard arguments.count >= 3 else {
  fputs("Usage: swift generate_app_icons.swift <output_path> <size>\n", stderr)
  exit(1)
}

let outputPath = arguments[1]
guard let sizeValue = Double(arguments[2]) else {
  fputs("Invalid size: \(arguments[2])\n", stderr)
  exit(1)
}

let canvasSize = NSSize(width: sizeValue, height: sizeValue)
let rect = NSRect(origin: .zero, size: canvasSize)
let radius = sizeValue * 0.28

let image = NSImage(size: canvasSize)
image.lockFocus()

guard let context = NSGraphicsContext.current?.cgContext else {
  fputs("Unable to create graphics context\n", stderr)
  exit(1)
}

context.setAllowsAntialiasing(true)
context.setShouldAntialias(true)

let roundedPath = NSBezierPath(
  roundedRect: rect,
  xRadius: radius,
  yRadius: radius
)
roundedPath.addClip()

let backgroundGradient = NSGradient(
  colors: [
    NSColor(calibratedRed: 0.09, green: 0.30, blue: 0.25, alpha: 1.0),
    NSColor(calibratedRed: 0.18, green: 0.48, blue: 0.36, alpha: 1.0),
    NSColor(calibratedRed: 0.56, green: 0.82, blue: 0.55, alpha: 1.0),
  ]
)
backgroundGradient?.draw(in: roundedPath, angle: 42)

func drawCircle(x: CGFloat, y: CGFloat, diameter: CGFloat, color: NSColor) {
  let circleRect = NSRect(x: x, y: y, width: diameter, height: diameter)
  color.setFill()
  NSBezierPath(ovalIn: circleRect).fill()
}

drawCircle(
  x: sizeValue * 0.66,
  y: sizeValue * 0.70,
  diameter: sizeValue * 0.42,
  color: NSColor(calibratedRed: 0.95, green: 0.97, blue: 0.75, alpha: 0.42)
)

func drawDot(x: CGFloat, y: CGFloat, diameter: CGFloat) {
  let rect = NSRect(x: x, y: y, width: diameter, height: diameter)
  let border = NSBezierPath(ovalIn: rect)
  NSColor(calibratedRed: 0.95, green: 0.98, blue: 0.76, alpha: 0.72).setStroke()
  border.lineWidth = diameter * 0.08
  border.stroke()

  let fillRect = rect.insetBy(dx: diameter * 0.08, dy: diameter * 0.08)
  NSColor(calibratedRed: 0.61, green: 0.84, blue: 0.50, alpha: 1.0).setFill()
  NSBezierPath(ovalIn: fillRect).fill()
}

drawDot(
  x: sizeValue * 0.16,
  y: sizeValue * 0.66,
  diameter: sizeValue * 0.11
)
drawDot(
  x: sizeValue * 0.10,
  y: sizeValue * 0.51,
  diameter: sizeValue * 0.095
)
drawDot(
  x: sizeValue * 0.06,
  y: sizeValue * 0.36,
  diameter: sizeValue * 0.085
)

func drawBand(y: CGFloat, height: CGFloat, width: CGFloat, angle: CGFloat, colors: [NSColor]) {
  context.saveGState()
  context.translateBy(x: rect.midX, y: rect.midY)
  context.rotate(by: angle)
  context.translateBy(x: -rect.midX, y: -rect.midY)

  let bandRect = NSRect(
    x: -sizeValue * 0.04,
    y: y,
    width: width,
    height: height
  )
  let bandPath = NSBezierPath(
    roundedRect: bandRect,
    xRadius: height / 2,
    yRadius: height / 2
  )
  bandPath.addClip()

  let gradient = NSGradient(colors: colors)
  gradient?.draw(in: bandPath, angle: 0)
  context.restoreGState()
}

drawBand(
  y: sizeValue * 0.42,
  height: sizeValue * 0.16,
  width: sizeValue * 1.05,
  angle: -0.34,
  colors: [
    NSColor.clear,
    NSColor(calibratedRed: 0.74, green: 0.90, blue: 0.54, alpha: 1.0),
    NSColor(calibratedRed: 0.92, green: 0.97, blue: 0.66, alpha: 1.0),
  ]
)

drawBand(
  y: sizeValue * 0.28,
  height: sizeValue * 0.15,
  width: sizeValue * 1.02,
  angle: -0.34,
  colors: [
    NSColor.clear,
    NSColor(calibratedRed: 0.52, green: 0.80, blue: 0.49, alpha: 1.0),
    NSColor(calibratedRed: 0.80, green: 0.92, blue: 0.55, alpha: 1.0),
  ]
)

let symbolParagraph = NSMutableParagraphStyle()
symbolParagraph.alignment = .center

let shadow = NSShadow()
shadow.shadowBlurRadius = sizeValue * 0.08
shadow.shadowOffset = NSSize(width: sizeValue * 0.01, height: -sizeValue * 0.02)
shadow.shadowColor = NSColor(calibratedWhite: 0.0, alpha: 0.16)

let note = NSAttributedString(
  string: "♪",
  attributes: [
    .font: NSFont.systemFont(ofSize: sizeValue * 0.68, weight: .bold),
    .foregroundColor: NSColor(calibratedRed: 1.0, green: 0.985, blue: 0.95, alpha: 1.0),
    .paragraphStyle: symbolParagraph,
    .shadow: shadow,
  ]
)

let noteRect = NSRect(
  x: sizeValue * 0.22,
  y: sizeValue * 0.13,
  width: sizeValue * 0.56,
  height: sizeValue * 0.66
)
note.draw(in: noteRect)

image.unlockFocus()

guard
  let tiffData = image.tiffRepresentation,
  let bitmap = NSBitmapImageRep(data: tiffData),
  let pngData = bitmap.representation(using: .png, properties: [:])
else {
  fputs("Unable to encode PNG data\n", stderr)
  exit(1)
}

try pngData.write(to: URL(fileURLWithPath: outputPath))
