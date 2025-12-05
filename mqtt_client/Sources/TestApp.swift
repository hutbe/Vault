//
//  File.swift
//  MQTTServerApp
//
//  Created by hut on 2025/12/5.
//

import Foundation


class TestApp {
    func run() {
        print("Test App is Runging ....")
        
//         simpleGetRequest { result in
//             switch result {
//             case .success(let json):
//                 print("Response: \(json)")
//             case .failure(let error):
//                 print("Error: \(error)")
//             }
//         }
        
        RunLoop.main.run()
    }

//     func simpleGetRequest(completion: @escaping (Result<[String: Any], Error>) -> Void) {
//         guard let url = URL(string: "http://localhost:9090") else {
//             completion(.failure(NSError(domain: "Invalid URL", code: 400)))
//             return
//         }
//
//         URLSession.shared.dataTask(with: url) { data, _, error in
//             if let error = error {
//                 completion(.failure(error))
//                 return
//             }
//
//             guard let data = data,
//                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
//                 completion(.failure(NSError(domain: "Invalid response", code: 500)))
//                 return
//             }
//
//             completion(.success(json))
//         }.resume()
//     }

}
