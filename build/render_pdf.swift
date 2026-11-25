import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
// Render one page of a PDF to a grayscale PNG (used by salvage_scan.py for JBIG2 masks).
// render_pdf in.pdf out.png [scale=3] [page=1]   Build: swiftc -O build/render_pdf.swift -o build/render_pdf
let a = CommandLine.arguments
guard let doc = CGPDFDocument(URL(fileURLWithPath: a[1]) as CFURL), let page = doc.page(at: Int(CommandLine.arguments.count > 4 ? CommandLine.arguments[4] : "1")!) else { print("bad pdf"); exit(1) }
let s = CGFloat(Double(a[3]) ?? 3.0)
let r = page.getBoxRect(.mediaBox)
let w = Int(r.width * s), h = Int(r.height * s)
let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceGray(), bitmapInfo: CGImageAlphaInfo.none.rawValue)!
ctx.setFillColor(gray: 1, alpha: 1); ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
ctx.scaleBy(x: s, y: s); ctx.drawPDFPage(page)
let img = ctx.makeImage()!
let dst = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[2]) as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dst, img, nil); CGImageDestinationFinalize(dst)
