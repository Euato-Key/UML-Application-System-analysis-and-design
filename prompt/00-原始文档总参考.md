以下为示例实验过程。
阶段1.业务获取
1.1.目标
· 把“口述需求”→用例图+业务术语表
1.2.步骤
① 访谈录音（2 人一组，手机录音 5 min 以内）。示例需求：
“我们是校医院，想做一个‘智能候诊系统’，学生扫码签到后能查看前面还有几个人，医生能叫号，护士能维护科室信息……”
② 语音转文本。用“飞书妙记”一键转文字，导出 md。
③Prompt示例：
你是一名业务分析师，请从以下原始访谈文本中：
1. 抽取参与者（Actor）与业务用例（用动词+名词短语），输出PlantUML格式用例图；
2. 用表格列出业务术语<术语, 描述, 同义词>；
3. 用中文，不要出现“系统”二字（仅业务用例）。
文本如下：
===
{{ 粘贴访谈md }}
===
输出格式：
@startuml
left to right direction
actor 学生
...
@enduml
④ 一键出图
把LLM返回的PlantUML粘到VS Code，Alt+D 即可看到用例图。
⑤ 校验清单（小组互评）
□ 有没有遗漏“时间”型参与者？
□ 用例是否都是“动词+名词”？
□ 医生/护士是否重复？→ 可归为“医务人员”
阶段2.需求建模
2.1.目标
· 生成“功能清单+用例详情+首版UML”
2.2.步骤
① 用例分级Prompt（示例）
针对上述用例图，请：
1. 按“学生、医生、护士”三个参与者，输出功能清单（一级功能→二级功能）；
2. 选 3 个核心用例，输出用例详述（主成功场景 7 步以内，扩展场景 3 条以内）；
3. 为每个用例画出 PlantUML 活动图（swimlane 按参与者分）。
② LLM 返回后，人工只做 2 件事
· 把明显错误场景删掉；
· 在活动图里补充“业务规则”备注。
③ 生成系统级用例图（加边界框）
Prompt：
把业务用例图映射到系统用例，边界框命名为“智能候诊系统”，保留相同参与者，用例名前加“UC”前缀，输出PlantUML。
阶段3.系统架构与构件
3.1.目标
· 得到首版类图+包图+序列图，并建立“需求→类”追踪边
3.2.步骤
① 类图草图Prompt
根据用例详述，请：
1. 输出候选实体类（仅类名+主要属性+关联多重性）；
2. 用 PlantUML 类图表示；
3. 为每个类增加一行“需求追踪：对应用例编号”。
② 手工微调（15 min）
· 把“签到记录”拆成“签到记录”+“排队序号”两个类；
· 补充“科室-医生”1:n 关联。
③ 序列图（每个用例描述核心场景）
Prompt：
针对“学生扫码签到”主成功场景，画出 PlantUML 序列图，对象：学生、扫码页面、签到控制器、签到记录、排队计算器。
④ 知识图谱入库（自动脚本）
python kg_build.py --stage design --files *.puml
脚本自动解析 PlantUML，生成节点（UseCase/Class/Operation）与边（trace/dependency），Neo4j 浏览器可见。
阶段4.代码骨架与双向追踪
4.1.目标
· 生成可运行 Spring-Boot 骨架（Java）或 FastAPI（Python），并建立“类→代码”双向追踪
4.2.步骤
① Prompt（以 Java 为例）
根据以下类图，生成 Spring-Boot 代码要求：
- 使用 JPA 实体注解
- 为每个类生成 CRUD Controller
- 在注释里插入 “@trace UCxx” 标记
输出完整可编译目录结构，用 code-block 分文件给出。
② 本地 build
mvn package
java -jar target/ood-0.0.1-SNAPSHOT.jar
访问 http://localhost:8080/swagger-ui.html 能看到 API 即可。
③ 反向追踪脚本
python kg_trace.py --direction both --code src/main/java
脚本扫描 @trace 注释，自动在 Neo4j 中建立“CodeFile-implement->Class” 边，实现“需求-类-代码” 三级跳转。
阶段5.变更管理
5.1.场景
“护士说：我们还需要支持‘预约签到’，提前 1 天扫码也算有效。”
5.2.一键影响分析
① 在 Neo4j 浏览器执行脚本（已模板化）
:play https://raw.githubusercontent.com/nju-ics/ood-llm-lab/main/change_impact.cypher
输入变更用例编号 UC05，一键高亮所有受影响类、方法、测试用例。
② 人工确认后，Prompt 增量生成
5.3.为支持“预约签到”，请：
1. 在类图新增“Appointment”类，与“签到记录”关联；
2. 生成增量 SQL（MySQL）；
3. 生成单元测试（JUnit5）。