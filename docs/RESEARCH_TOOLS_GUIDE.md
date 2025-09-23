# 🔍 Research Tools Guide for LibreChat

## Overview

LibreChat được tích hợp với Research AI Agent thông qua MCP (Model Context Protocol), cung cấp khả năng nghiên cứu và phân tích mạnh mẽ.

## 🛠️ Available Research Tools

### 1. **research_quick** 
- **Mục đích**: Nghiên cứu nhanh và tóm tắt thông tin
- **Output**: Báo cáo ngắn gọn với key findings và insights
- **Thời gian**: ~30-60 giây

### 2. **research_comprehensive**
- **Mục đích**: Phân tích toàn diện với methodology chi tiết  
- **Output**: Báo cáo đầy đủ với executive summary, findings, recommendations
- **Thời gian**: ~1-2 phút

## 🎯 Cách sử dụng

### Phương pháp 1: Chat trực tiếp
```
Tôi cần nghiên cứu về AI trends 2024
```
```
Hãy phân tích comprehensive về thị trường fintech Việt Nam
```

### Phương pháp 2: Sử dụng Research Agents
1. Chọn **"Research Assistant"** agent từ dropdown
2. Agent được pre-configured để hiển thị đầy đủ tool output
3. Chat như bình thường

### Phương pháp 3: Direct tool calls
```
@research_quick Machine learning trends
```
```
@research_comprehensive Blockchain adoption in banking
```

## ✅ Đảm bảo hiển thị đầy đủ Tool Output

### 1. **Sử dụng Research Agents**
- Research Assistant và Strategic Analyst được config để hiển thị full output
- Không summarize hay truncate tool responses

### 2. **System Prompts được tối ưu**
LibreChat config với instructions:
- Hiển thị COMPLETE tool output
- Maintain original formatting
- Preserve emojis và structure
- Show ALL sections từ research reports

### 3. **Interface Settings**
- `maxMessageLength: 50000` - Increase message limit
- `preserveToolFormatting: true` - Maintain formatting
- `allowMarkdown: true` - Support markdown trong responses

## 📊 Expected Output Format

### Quick Research Output:
```
🔍 **Quick Research: [topic]**

📊 **Key Findings:**
• Research insights
• Data analysis
• Trend identification

🎯 **Summary:**
[Comprehensive analysis]

💡 **Key Insights:**
• Market dynamics
• Innovation drivers
• Future outlook

📈 **Recommendations:**
• Action items
• Strategic considerations
```

### Comprehensive Research Output:
```
📋 **Comprehensive Research Report: [topic]**

🎯 Executive Summary
[Deep analysis overview]

🔬 Research Methodology
✅ Phase 1: Data collection
✅ Phase 2: Analysis
✅ Phase 3: Synthesis  
✅ Phase 4: Recommendations

📊 Key Findings
[Detailed findings with sections]

🎯 Strategic Recommendations
🚀 Immediate Actions (0-3 months)
📅 Medium-term Strategy (3-12 months)
🔮 Long-term Vision (12+ months)

💡 Key Takeaways
[Summary and conclusions]
```

## 🐛 Troubleshooting

### Tool output bị truncate
**Symptoms**: Chỉ thấy "Ran research_comprehensive" thay vì full report

**Solutions**:
1. ✅ Use Research Assistant agent (pre-configured)
2. ✅ Check agent instructions include "display complete output"
3. ✅ Ensure LibreChat config có `maxMessageLength: 50000`
4. ✅ Verify `preserveToolFormatting: true`

### Tool không hoạt động
**Check**:
```bash
# Verify MCP connection
docker-compose logs api | grep research_ai_agent

# Should see:
# ✅ Tools: research_quick, research_comprehensive
# ✅ Added 2 MCP tools
```

### Format bị mất
**Solutions**:
- Ensure `allowMarkdown: true` trong config
- Use Research Assistant agent thay vì custom agents
- Check system prompts include formatting preservation

## 🔧 Advanced Usage

### Custom Research Focus
```
Research comprehensive về "AI in healthcare" với focus area "regulatory compliance"
```

### Multi-step Research
```
1. Quick research về market size
2. Comprehensive analysis về competitive landscape  
3. Strategic recommendations cho market entry
```

### Research với Context
```
Dựa trên document đã upload, hãy research comprehensive về industry trends
```

## 🎯 Best Practices

1. **Specify research scope**: Càng cụ thể càng tốt
2. **Use appropriate tool**: Quick cho overview, Comprehensive cho detailed analysis
3. **Use Research Agents**: Pre-configured để optimal output display
4. **Review full output**: Tool responses contain valuable structured information
5. **Follow up questions**: Ask for clarification sau khi review tool output

## 📈 Performance Tips

- **Quick research**: Cho preliminary assessment
- **Comprehensive research**: Cho strategic planning và detailed analysis
- **Combine tools**: Start với quick, follow up với comprehensive nếu cần
- **Context awareness**: Mention previous research trong follow-up queries

---

**Research AI Agent Integration thành công! 🚀**
