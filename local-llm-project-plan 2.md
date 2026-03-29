# PropSwift 本地LLM部署方案

## 1. 项目背景

PropSwift 是一个英国住宅租赁平台产品。系统会收到申请人的邮件，需要自动完成邮件分类、信息提取、listing匹配等任务。

### 1.1 当前架构

当前pipeline使用OpenAI API，分为两条处理线：

- **文字处理线（GPT-4o Mini）：** 处理邮件正文，完成分类和基本字段提取。成本极低，效果很好。包含三个LLM调用（详见第4节）。
- **附件处理线（GPT Vision）：** 处理申请人提交的图片/PDF附件（工资单、税表、银行流水等），提取收入、工作类型、居住人数、宠物等详细字段。这部分是API成本的大头。

### 1.2 本地化动机

- **数据隐私：** 租房申请包含姓名、收入、地址等PII信息，本地处理更安全。
- **减少外部依赖：** 降低对第三方API服务的依赖风险。
- **学习与技术探索：** 了解本地LLM部署的完整流程。

> 注意：本地化的目标不是降低成本——GPT-4o Mini已经非常便宜。主要驱动力是隐私和独立性。

---

## 2. 硬件环境

### 2.1 当前开发测试机

- **机型：** MacBook Pro M1 Max
- **内存：** 64GB 统一内存
- **内存带宽：** ~400GB/s
- **能力：** 可同时加载两个模型（14B + 视觉模型），运行非常舒适
- **用途：** 开发、测试、验证方案可行性
- **注意：** 目前处于测试阶段，不会一直开着服务，有时需要做其他事情会关掉LLM服务

### 2.2 未来部署机（远期计划）

- **机型：** Mac Mini M4 或 M5
- **内存：** 32GB 统一内存
- **内存带宽：** ~100GB/s（显著低于M1 Max）
- **能力：** 可运行14B Q4量化模型（~9GB），速度比M1 Max慢2-3倍，但对邮件处理场景完全够用
- **影响：** 模型选型需要确保在32GB机器上也能运行

---

## 3. 技术选型

### 3.1 推理引擎：Ollama

选择Ollama作为统一推理引擎，理由：

- 对Apple Silicon的Metal加速支持最成熟
- 自带OpenAI兼容API（`http://localhost:11434/v1/chat/completions`）
- 原生支持JSON Schema约束输出（通过GBNF grammar在token生成层面强制格式）
- 所有模型通过同一套API访问，切换模型只需改model参数
- 安装简单，模型管理方便
- 社区活跃，文档丰富

### 3.2 文字处理模型：Qwen 3 14B

- **Ollama命令：** `ollama pull qwen3:14b`
- **量化格式：** Q4_K_M（默认）
- **内存占用：** ~9GB
- **选择理由：**
  - 14B级别综合能力最强（截至2026年初）
  - 指令遵从和结构化输出表现优秀
  - 支持thinking/non-thinking模式切换（本项目使用non-thinking模式，速度更快）
  - Q4量化后在64GB和未来32GB机器上都能舒适运行
  - 邮件是自由格式的，14B在理解不规范文本上比8B更稳定
- **备选：** Phi-4 14B（微软，MIT许可，推理能力强但上下文窗口仅16K，优势不对口）

### 3.3 视觉处理模型（第二阶段）

两个候选方案，等第一阶段跑通后用真实附件样本对比测试再决定：

**方案A：分步走（OCR + 文字模型）**

- 第一步用 **GLM-OCR（0.9B，~2.2GB）** 提取图片中的文字
- 第二步将提取的文字喂给 Qwen 3 14B 做结构化信息提取
- 优势：各模型做自己最擅长的事，GLM-OCR在纯文字提取上的OCR基准测试排名第一（OmniDocBench V1.5得分94.62）
- 适合：清晰的打印文档、PDF

**方案B：一步到位（视觉语言模型）**

- 直接用 **Qwen2.5-VL 7B（~8-9GB）** 看图并提取结构化信息
- 优势：pipeline更简单，一个调用完成OCR和理解
- 适合：需要理解文档布局和上下文的场景

**关键约束：** 不使用多模态模型处理纯文字邮件。多模态模型的参数有一部分用于视觉能力，同等参数量下纯文字任务表现不如专门的文字模型。文字归文字模型，图片归视觉模型，各司其职。

### 3.4 内存管理

- 在64GB机器上设置 `OLLAMA_MAX_LOADED_MODELS=2`，让文字模型和视觉模型同时驻留内存
- 避免模型切换时的冷启动延迟（否则每次切换需要几秒到十几秒加载时间）
- 32GB机器上也放得下两个模型（14B约9GB + 视觉模型2-9GB，总共不超过20GB）

---

## 4. Pipeline详细设计

### 4.1 第一阶段：文字处理Pipeline（当前目标）

三个LLM调用，全部使用 Qwen 3 14B，通过Ollama同一个API endpoint，只是prompt不同。

#### 调用1：邮件分类器（核心）

- **功能：** 将邮件分为7个阶段（initial_interest / viewing_request / post_viewing / document_submission / questionnaire_reply / offer / unknown），同时提取 full_name、property_reference、mentioned_rent
- **输入：** sender display name + subject + body preview（前500字符）+ attachment filenames
- **输出：** 扁平JSON，5个字段
- **输出约束：** 使用Ollama的JSON Schema format参数强制输出格式
- **关键逻辑：**
  - 根据附件文件名关键词判断document_submission阶段
  - 区分rent和income（仅提取房租，不提取申请人收入）
  - full_name需综合判断sender name、正文自我介绍和签名

#### 调用2：Listing匹配器

- **功能：** 将调用1提取的property_reference与数据库中已有listing匹配
- **输入：** property_reference + listing列表
- **输出：** 一个UUID字符串或"NEW"
- **复杂度：** 最低，本质是模糊字符串匹配

#### 调用3：命令解析器

- **功能：** 解析房产中介发给系统的操作指令
- **输入：** 中介邮件内容
- **输出：** JSON（command_type + listing_reference + parameters + refusal_reason）
- **分类数：** 9个命令类型（RESEND_REPORT / SET_CRITERIA / DELETE_APPLICANT / EXTEND_RETENTION / LIST_STATUS / ENABLE_FORWARDING / DISABLE_FORWARDING / HELP / REFUSED）
- **特殊逻辑：** 涉及Equality Act 2010保护特征的请求需返回REFUSED

### 4.2 第二阶段：附件处理Pipeline（后续）

- 处理申请人提交的工资单、税表、银行流水、ID等附件
- 提取详细字段：收入、工作类型、居住人数、宠物等
- 使用视觉模型（GLM-OCR或Qwen2.5-VL，待测试确定）
- API调用方式与文字模型一致，仅需改model参数并在message中增加images字段

### 4.3 第三阶段：置信度路由（混合方案）

在附件处理阶段，实现本地优先、API兜底的路由机制：

**前置判断——图片质量检测：**

- 在调用视觉模型前，用图像处理检测清晰度、分辨率、对比度
- 清晰的PDF和高质量扫描件 → 本地处理
- 模糊的手机照片 → 直接走GPT Vision API
- 最可靠，不依赖LLM判断

**后置判断——提取完整度：**

- 本地模型处理完后，检查输出JSON字段完整度
- 关键字段（如收入、姓名）返回null过多 → fallback到GPT Vision重新处理
- 客观标准，不依赖模型自我评估

**辅助参考——模型自报置信度：**

- prompt中可让模型对每个字段给confidence分数
- 仅作为辅助参考，不作为唯一判断依据
- 小模型的自信度不一定可靠（提错了也可能给高分）

---

## 5. 输出格式与JSON Schema约束

### 5.1 机制说明

Ollama支持在API调用时传入JSON Schema，通过GBNF grammar在token生成层面强制模型只产生符合指定schema的JSON。这意味着：

- 不依赖模型"自觉"遵守格式
- 即使小模型也能稳定输出合法JSON
- 不会出现格式错乱、多余的前缀文字等问题
- 与GPT-4o Mini的structured output机制类似

### 5.2 调用示例

```python
import requests

# 邮件分类器调用示例
response = requests.post("http://localhost:11434/api/chat", json={
    "model": "qwen3:14b",
    "messages": [
        {"role": "system", "content": "分类器system prompt..."},
        {"role": "user", "content": "邮件内容..."}
    ],
    "stream": False,
    "format": {
        "type": "object",
        "properties": {
            "email_phase": {
                "type": "string",
                "enum": ["initial_interest", "viewing_request", "post_viewing",
                         "document_submission", "questionnaire_reply", "offer", "unknown"]
            },
            "confidence": {"type": "number"},
            "property_reference": {"type": ["string", "null"]},
            "mentioned_rent": {"type": ["number", "null"]},
            "full_name": {"type": ["string", "null"]}
        },
        "required": ["email_phase", "confidence", "property_reference",
                      "mentioned_rent", "full_name"]
    }
})
```

### 5.3 最佳实践

- 在prompt中也描述期望的JSON格式，同时通过format参数约束——双重保障
- 使用 `temperature: 0`（或极低值）最大化schema遵从性
- 验证返回结果，如果解析失败则重试

---

## 6. 测试结果记录

### 6.1 环境配置

- macOS Sonoma 14（从Ventura 13升级）
- Ollama安装正常，Qwen 3 14B (Q4_K_M) 拉取成功
- Thinking模式通过API参数 `"think": false` 关闭（不是通过prompt，是Ollama原生参数）

### 6.2 调用1：邮件分类器 — ✅ 验证通过

**模拟邮件（12封）：**

| 指标 | 结果 |
|---|---|
| 分类准确率 | 10/12（两个viewing_request vs initial_interest是业务定义边界case，可接受） |
| 字段提取 | rent vs income区分全部正确；full_name全部正确（修复title case后） |
| 平均响应时间 | ~3.3秒/封 |

**真实邮件（15封）：**

| 指标 | 结果 |
|---|---|
| 分类准确率 | 11/15（2个viewing_request边界case可接受；1个questionnaire_reply暂不处理；1个document_submission已通过prompt修复） |
| 字段提取 | rent vs income区分全部正确 |
| 平均响应时间 | ~3.7秒/封 |

**prompt修复记录：**
- document_submission规则增加了"Future intent to send does NOT count"条款，修复TEST 11误判

### 6.3 调用2：Listing匹配器 — ✅ 验证通过

- 代码评分逻辑覆盖了绝大部分情况，几乎不触发LLM fallback
- 有地址的邮件全部通过代码评分正确匹配
- 无地址邮件正确走fallback逻辑
- 无匹配listing时正确触发auto_create

### 6.4 调用3：Applicant Ranking — ⚠️ 排序正确，计分不准

**测试配置：** 1个listing（£1,500/月），5个applicant（强/中/弱/自雇/无信息）

**结果：**

| Applicant | 预期Tier | 实际Tier | 预期分数区间 | 实际分数 | 排名 |
|---|---|---|---|---|---|
| Alice Smith (verified, permanent) | 🟢 Strong | 🟢 Strong | 75-100 | 100 | #1 ✓ |
| David Chen (self-employed, advance rent) | 🟡 Possible | 🟢 Strong | 50-85 | 80 | #2 |
| Ben Taylor (self-reported, permanent) | 🟡 Possible | 🟢 Strong | 50-79 | 70 | #3 |
| Chloe Adams (part-time, low income) | 🔴 Weak | 🟡 Possible | 0-49 | 50 | #4 |
| Emma Jones (no data) | ⚪ Insufficient | ⚪ Insufficient | 0-30 | 0 | #5 ✓ |

**问题分析：**
- **排序能力：好。** 5个applicant的相对顺序完全正确
- **精确计分：差。** 扣分规则没有严格执行：
  - Alice缺3个supporting doc但得了满分（应扣15分）
  - Chloe年收入£21,600 vs 要求£45,000，14.4×远低于18×，affordability应扣60分但只扣了很少
  - 宠物被错误标记为red_flag
- **根本原因：** 确定性计算（数学、条件分支）不应该交给LLM，即使GPT-4o也有同样问题
- **响应时间：** 82秒（5个applicant），可接受（每晚批处理任务）

**后续重构方向（已确认，待实施）：**
- 代码层做确定性计算：affordability扣分、employment扣分、document缺失检查、基础分数
- LLM层只做需要判断的部分：summary生成、anomaly/red flag识别、key_details整理
- 这个拆分不论最终用GPT-4o还是本地模型都会更可靠

---

## 7. API服务化

### 7.1 本地访问

Ollama默认监听 `http://localhost:11434`，本机直接使用。

### 7.2 局域网访问

让局域网内其他电脑访问：

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

之后局域网内其他电脑用MBP的局域网IP访问：`http://192.168.1.xxx:11434`

长期生效需写入Ollama的launchd配置。暴露到公网需加反向代理和鉴权。

### 7.3 多模型内存管理

```bash
# 允许同时加载2个模型（文字模型 + 视觉模型）
export OLLAMA_MAX_LOADED_MODELS=2
```

### 7.4 关键API参数备忘

| 参数 | 用途 | 值 |
|---|---|---|
| `think` | 关闭thinking模式 | `false` |
| `stream` | 非流式输出 | `false` |
| `format` | JSON Schema约束 | schema dict |
| `model` | 模型名 | `qwen3:14b` |

---

## 8. 执行计划（更新版）

### 第一阶段：文字Pipeline本地化 — ✅ 已完成

1. ✅ macOS升级到Sonoma 14
2. ✅ 安装Ollama
3. ✅ 拉取Qwen 3 14B
4. ✅ 关闭thinking模式（`"think": false`）
5. ✅ 适配邮件分类器prompt + JSON Schema约束
6. ✅ 适配Listing匹配器（代码评分 + LLM fallback）
7. ✅ 模拟邮件测试通过
8. ✅ 真实邮件测试通过
9. ✅ prompt修复（document_submission将来时误判）

### 第一阶段补充：Ranking本地化 — 🔶 流程跑通，待重构

1. ✅ 适配ranking prompt + JSON Schema约束
2. ✅ 测试通过（排序正确，计分偏高）
3. 🔲 重构：拆分确定性计算（代码）和判断性任务（LLM）

### 第二阶段：附件处理本地化 — 🔲 待开始

1. 🔲 拉取视觉模型（GLM-OCR和/或Qwen2.5-VL）
2. 🔲 用真实附件样本测试OCR效果
3. 🔲 对比GPT Vision输出
4. 🔲 决定分步走（OCR+文字模型）还是一步到位（视觉语言模型）

### 第三阶段：混合路由 — 🔲 待开始

1. 🔲 实现图片质量前置检测
2. 🔲 实现提取完整度后置判断
3. 🔲 本地优先、API兜底的路由逻辑

### 第四阶段：集成到生产系统 — 🔲 待开始

1. 🔲 将Ollama API调用封装为和OpenAI API兼容的接口
2. 🔲 在FastAPI后端增加本地/远程切换逻辑
3. 🔲 部署到Mac Mini（远期）

---

## 9. 风险与注意事项

- **准确率可能小幅下降：** 邮件分类器实测准确率很高，接近GPT-4o Mini。Ranking的计分需要重构为代码+LLM混合方案。
- **prompt敏感度：** 本地模型对prompt措辞更敏感，已验证需要更精确的规则描述（如document_submission的将来时修复）。
- **服务可用性：** MBP合盖休眠会中断服务。未来部署到Mac Mini可缓解。
- **模型更新：** Qwen 3 14B目前表现良好，但开源模型迭代快。Ollama切换模型只需一行命令。
- **Thinking模式：** 必须在每个API调用中显式设置 `"think": false`，否则会生成无用的思考token，增加延迟。

---

## 10. 文件清单

```
propswift-local-llm/
├── test_pipeline.py        # 主测试脚本（分类器 + Listing匹配 + Ranking）
├── test_emails.py          # 12封模拟测试邮件
├── test_emails_real.py     # 15封真实测试邮件
├── test_listings.py        # 10条模拟listing
├── test_ranking_data.py    # 5个模拟applicant（ranking测试用）
├── prompts.py              # 所有system prompt
├── schemas.py              # JSON Schema定义
└── README.md               # 使用说明
```
