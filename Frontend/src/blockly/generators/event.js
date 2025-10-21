import { pythonGenerator } from 'blockly/python';
import * as Blockly from "blockly/core";
import { need } from './prelude'

// 简单缩进工具（仅用于本文件内需要时）
function indent(s) {
  if (!s) return ''
  s = String(s).replace(/^\s*\n+|\n+\s*$/g, '')
  const pref = (pythonGenerator && pythonGenerator.INDENT) ? pythonGenerator.INDENT : '  '
  return s.split('\n').map(l => (l ? pref + l : '')).join('\n') + (s ? '\n' : '')
}

export const defineEventGenerators = () => {
  pythonGenerator.forBlock['event_gameStart'] = function(block) {
    return `CoronaEngine.gameStart()\n`;
  };
  
  pythonGenerator.forBlock['event_keyboard'] = function(block) {
    // 当使用键盘事件积木时，需要键盘前置片段
    need('keyboard')
    const key = block.getFieldValue('x') || ''
    // 仅在存在 DO 输入时调用 statementToCode，避免 "Input \"DO\" doesn't exist" 的异常
    let branch = ''
    if (block.getInput && block.getInput('DO')) {
      // statementToCode 可能返回空字符串
      branch = pythonGenerator.statementToCode(block, 'DO') || ''
    }
    if (!branch) {
      const indentUnit = (pythonGenerator && pythonGenerator.INDENT) ? pythonGenerator.INDENT : '  '
      branch = indentUnit + 'pass\n'
    }
    // 将该事件标记行输出到 handler 中（由 index.js 负责路由到 def handle）
    // 后续串联的语句将自动附加在本块之后，属于 handler 函数体
    return `if key == '${key}':\n` + indent(branch);
  };
  
  pythonGenerator.forBlock['event_RB'] = function(block) {
    const x = block.getFieldValue('x');
    return `CoronaEngine.RB("${x}")\n`;
  };
  
  pythonGenerator.forBlock['event_broadcast'] = function(block) {
    const x = block.getFieldValue('x');
    return `CoronaEngine.broadcast("${x}")\n`;
  };
  
  pythonGenerator.forBlock['event_broadcastWait'] = function(block) {
    const x = block.getFieldValue('x');
    return `CoronaEngine.broadcastWait("${x}")\n`;
  };
  
  pythonGenerator.forBlock['event_keyboard_combo'] = function(block) {
    // 组合键事件：同样路由到 handler
    need('keyboard')
    var combo = block.getFieldValue('combo') || '';
    return `# 组合键事件: ${combo}\n`;
  };

// 鼠标点击事件
  pythonGenerator.forBlock['event_mouse_click'] = function(block) {
    // 中文注释：生成鼠标点击事件处理函数
    var button = block.getFieldValue('button');
    var code = `# 当鼠标点击${button}时触发\n`;
    code += `def on_mouse_click_${button}():\n`;
    code += `    pass  # 在此处编写事件处理逻辑\n`;
    return code;
  };

// 鼠标移动事件
  pythonGenerator.forBlock['event_mouse_move'] = function(block) {
    // 中文注释：生成鼠标移动事件处理函数
    var code = `# 当鼠标移动时触发\n`;
    code += `def on_mouse_move(x, y):\n`;
    code += `    pass  # 在此处编写事件处理逻辑\n`;
    return code;
  };

// 鼠标滚轮事件
  pythonGenerator.forBlock['event_mouse_wheel'] = function(block) {
    // 中文注释：生成鼠标滚轮事件处理函数
    var code = `# 当鼠标滚轮滚动时触发\n`;
    code += `def on_mouse_wheel(delta):\n`;
    code += `    pass  # 在此处编写事件处理逻辑\n`;
    return code;
  };

// 鼠标右键菜单事件
  pythonGenerator.forBlock['event_mouse_contextmenu'] = function(block) {
    // 中文注释：生成鼠标右键菜单事件处理函数
    var code = `# 当鼠标右键菜单时触发\n`;
    code += `def on_mouse_contextmenu(x, y):\n`;
    code += `    pass  # 在此处编写事件处理逻辑\n`;
    return code;
  };
}