//
//  TestApp.swift
//  MQTTServerApp
//
//  Created by hut on 2025/12/5.
//

import Foundation


class TestApp {
    func run() {
        print("Test App is Running ....")
        
        // 测试 iso8601ToMySQLTimestamp3 方法
        testIso8601ToMySQLTimestamp3()
        
//         simpleGetRequest { result in
//             switch result {
//             case .success(let json):
//                 print("Response: \(json)")
//             case .failure(let error):
//                 print("Error: \(error)")
//             }
//         }
        
        // RunLoop.main.run()
    }
    
    /// 测试 iso8601ToMySQLTimestamp3 函数
    func testIso8601ToMySQLTimestamp3() {
        print("\n========== 测试 iso8601ToMySQLTimestamp3 ==========\n")
        
        // 测试用例数组：[输入, 预期输出描述]
        let testCases: [(input: String, description: String)] = [
            // 标准 ISO8601 格式（带时区和毫秒）
            ("2025-12-09T08:00:00.123+08:00", "标准格式：带毫秒和+08:00时区"),
            ("2025-12-09T08:00:00.123Z", "标准格式：带毫秒和Z时区"),
            ("2025-12-09T00:00:00.999Z", "标准格式：毫秒999"),
            
            // 标准 ISO8601 格式（带时区，不带毫秒）
            ("2025-12-09T08:00:00+08:00", "标准格式：不带毫秒，+08:00时区"),
            ("2025-12-09T08:00:00Z", "标准格式：不带毫秒，Z时区"),
            ("2025-12-09T16:30:45-05:00", "标准格式：负时区-05:00"),
            
            // 不带时区的格式（将被当作UTC）
            ("2025-12-09T08:00:00.123", "无时区：带毫秒"),
            ("2025-12-09T08:00:00", "无时区：不带毫秒"),
            
            // 边界情况
            ("2025-01-01T00:00:00.000Z", "边界：年初"),
            ("2025-12-31T23:59:59.999Z", "边界：年末"),
            ("2025-10-21 20:50:50", "常用可读格式")
        ]
        
        let invalidTestCases: [(input: String, description: String)] = [
            // 错误格式（应该返回 nil）
            ("invalid-date", "无效格式：纯文本"),
            ("2025-12-09", "无效格式：只有日期"),
            ("", "无效格式：空字符串"),
        ]
        
        var successCount = 0
        var failCount = 0
        
        for (index, testCase) in testCases.enumerated() {
            print("测试 \(index + 1): \(testCase.description)")
            print("  输入: \(testCase.input)")
            
            if let result = iso8601ToMySQLTimestampNoMillis(testCase.input) {
                print("  ✅ 输出: \(result)")
                successCount += 1
            } else {
                print("  ❌ 输出: nil (解析失败)")
                failCount += 1
            }
            print()
        }
        
        for (index, invalidTestCase) in invalidTestCases.enumerated() {
            print("测试 \(index + 1): \(invalidTestCase.description)")
            print("  输入: \(invalidTestCase.input)")
            
            if let result = iso8601ToMySQLTimestampNoMillis(invalidTestCase.input) {
                print("  ❌ 输出: \(result)")
                failCount += 1
            } else {
                print("  ✅ 输出: nil (解析失败)")
                successCount += 1
            }
            print()
        }
        
        print("========== 测试总结 ==========")
        print("成功: \(successCount) 个")
        print("失败: \(failCount) 个")
        print("总计: \(testCases.count) 个测试用例")
        print("================================\n")
        
        // 额外：测试时区转换是否正确
        testTimezoneConversion()
    }
    
    /// 测试时区转换是否正确
    func testTimezoneConversion() {
        print("\n========== 测试时区转换 ==========\n")
        
        // 同一时刻的不同时区表示应该转换为相同的 UTC 时间
        let sameTimeDifferentTZ = [
            "2025-12-09T08:00:00+08:00",  // 北京时间 08:00
            "2025-12-09T00:00:00Z",       // UTC 00:00（同一时刻）
            "2025-12-08T19:00:00-05:00"   // 美东时间 前一天 19:00（同一时刻）
        ]
        
        print("测试：同一时刻的不同时区表示")
        var results: [String] = []
        for input in sameTimeDifferentTZ {
            if let result = iso8601ToMySQLTimestamp3(input) {
                results.append(result)
                print("  \(input) -> \(result)")
            }
        }
        
        // 检查结果是否一致
        if Set(results).count == 1 {
            print("\n✅ 时区转换正确：所有结果一致")
        } else {
            print("\n⚠️  时区转换可能有问题：结果不一致")
        }
        
        print("\n================================\n")
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
