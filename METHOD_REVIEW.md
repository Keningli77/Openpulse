# FAERS 方法核查记录

核查来源：FDA 官方网站源码仓库 FDA/open.fda.gov，提交
`a4b8fe1bf3119412d40dd086680459c94027955a`。
网页直接访问被云环境代理阻挡；通过平台 Git HTTPS 访问读取官方仓库。

## 已有文档依据

- `src/constants/fields/drugevent.yaml` 中 safetyreportversion：
  “openFDA will only return the latest version of a report.”
  同一报告更新版本不是在当前 API 中按多个版本分别计数。
- 同文件 receivedate：
  “Date that the report was _first_ received by FDA. If this report has multiple
  versions, this will be the date the first version was received by FDA.”
  当前范围是首次接收日期，不是事件发生日期或最近更新日期。
- `src/pages/apis/openfda-fields/index.tsx`：
  “Not all records have harmonized fields.”
  “Conversely, searching in these fields will only return a subset of records
  from a given endpoint.”
  单独查询标准化 generic_name 不能主张完整药物覆盖。

## 当前结果的准确描述

查询时 openFDA 中，首次接收日期处于 2022–2024 年的报告，使用平台当前
提供的最新版本，按标准化通用名匹配 empagliflozin，并按单一完整事件术语
Diabetic ketoacidosis 构建四格表。未限制药物角色或单方产品。
该结果不是截至 2024 年底冻结的历史报告内容。

最新版本处理不等于去除了不同报告 ID 下的同一患者/事件重复报告；不能主张
患者层面唯一识别。也不应为去重而直接排除 duplicate=1：该字段在官方文档中
表示存在较早版本，排除它会误删有效的最新报告。

## 尚待验证

药物短语匹配的实际覆盖；原始 medicinalproduct、通用名和商品名的匹配差异；
复方产品范围；报告角色定义；同一病例跨报告重复；事件术语范围。
额外查询须作为敏感性核查，不能无依据改变正式分析定义。

旧 audit/stats 的哈希关联应保持不变，不能为了更新说明直接改写旧 audit.json。
原报告的“API 版本处理未核查”现可由这份记录补充；未来代码与报告应更新说明。

官方链接：
- https://open.fda.gov/apis/drug/event/searchable-fields/
- https://open.fda.gov/apis/openfda-fields/
- https://github.com/FDA/open.fda.gov/blob/a4b8fe1bf3119412d40dd086680459c94027955a/src/constants/fields/drugevent.yaml
- https://github.com/FDA/open.fda.gov/blob/a4b8fe1bf3119412d40dd086680459c94027955a/src/pages/apis/openfda-fields/index.tsx
