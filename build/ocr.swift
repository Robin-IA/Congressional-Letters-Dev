// Usage: ocr IMAGE... -> one JSON line per image: {"image","text","confidence","lines"}
// OCR with Apple Vision, on-device. See OCR-TEST.md.
// Build: swiftc -O build/ocr.swift -o ocr
// Run:   ./ocr page1.png page2.png ...   (one JSON line per image)
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("{\"image\":\"\(path)\",\"error\":\"unreadable\"}"); continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    req.recognitionLanguages = ["en-US"]
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try handler.perform([req]) } catch {
        print("{\"image\":\"\(path)\",\"error\":\"\(error)\"}"); continue
    }
    let obs = req.results ?? []
    var lines: [String] = []; var conf: Float = 0
    for o in obs { if let c = o.topCandidates(1).first { lines.append(c.string); conf += c.confidence } }
    let out: [String: Any] = ["image": path, "text": lines.joined(separator: "\n"),
                              "confidence": obs.isEmpty ? 0 : Double(conf) / Double(obs.count),
                              "lines": lines.count]
    let data = try! JSONSerialization.data(withJSONObject: out)
    print(String(data: data, encoding: .utf8)!)
}
