import AppKit
import CoreGraphics
import Foundation
import ImageIO
import Vision

struct Item {
    let id: String
    let path: String
}

func jsonLine(_ object: [String: Any]) -> String {
    let data = try! JSONSerialization.data(withJSONObject: object, options: [])
    return String(data: data, encoding: .utf8)!
}

guard CommandLine.arguments.count == 4 else {
    fputs("usage: vision_audit dataset.jsonl release_root output.jsonl\n", stderr)
    exit(2)
}

let inputPath = CommandLine.arguments[1]
let releaseRoot = CommandLine.arguments[2]
let outputPath = CommandLine.arguments[3]
let content = try String(contentsOfFile: inputPath, encoding: .utf8)
let items = content.split(separator: "\n").compactMap { line -> Item? in
    guard let data = String(line).data(using: .utf8),
          let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let id = object["global_id"] as? String,
          let relative = object["image_path"] as? String else { return nil }
    let path = URL(fileURLWithPath: releaseRoot).appendingPathComponent(relative).path
    return Item(id: id, path: path)
}

FileManager.default.createFile(atPath: outputPath, contents: nil)
let handle = try FileHandle(forWritingTo: URL(fileURLWithPath: outputPath))
let lock = NSLock()
var completed = 0

DispatchQueue.concurrentPerform(iterations: items.count) { index in
    autoreleasepool {
        let item = items[index]
        let textRequest = VNRecognizeTextRequest()
        textRequest.recognitionLevel = .accurate
        textRequest.recognitionLanguages = ["zh-Hans", "en-US"]
        textRequest.usesLanguageCorrection = false
        textRequest.minimumTextHeight = 0.008
        let faceRequest = VNDetectFaceRectanglesRequest()
        var result: [String: Any]
        do {
            let imageURL = URL(fileURLWithPath: item.path)
            guard let source = CGImageSourceCreateWithURL(imageURL as CFURL, nil),
                  let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
                throw NSError(domain: "vision_audit", code: 1, userInfo: [NSLocalizedDescriptionKey: "image decode failed"])
            }
            let handler = VNImageRequestHandler(cgImage: image, options: [:])
            try handler.perform([textRequest, faceRequest])
            let observations = (textRequest.results ?? []).sorted {
                if abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.02 {
                    return $0.boundingBox.midY > $1.boundingBox.midY
                }
                return $0.boundingBox.minX < $1.boundingBox.minX
            }
            let textRows: [[String: Any]] = observations.compactMap { observation in
                guard let candidate = observation.topCandidates(1).first else { return nil }
                let b = observation.boundingBox
                return [
                    "text": candidate.string,
                    "confidence": candidate.confidence,
                    "box": [b.minX, b.minY, b.width, b.height]
                ]
            }
            let faces: [[Double]] = (faceRequest.results ?? []).map {
                let b = $0.boundingBox
                return [b.minX, b.minY, b.width, b.height]
            }
            result = ["global_id": item.id, "texts": textRows, "faces": faces, "error": NSNull()]
        } catch {
            result = ["global_id": item.id, "texts": [], "faces": [], "error": String(describing: error)]
        }
        let line = jsonLine(result) + "\n"
        lock.lock()
        handle.write(line.data(using: .utf8)!)
        completed += 1
        if completed % 50 == 0 {
            fputs("processed \(completed)/\(items.count)\n", stderr)
        }
        lock.unlock()
    }
}
try handle.close()
