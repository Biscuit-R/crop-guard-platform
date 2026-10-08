<template>
  <div class="qa-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">知识问答</h1>
        <p class="page-subtitle">描述虫害症状，支持连续追问；信息不足时助手会出选择题引导您补充</p>
      </div>
      <el-button v-if="messages.length" link type="primary" @click="resetChat">
        <el-icon><RefreshLeft /></el-icon>&nbsp;清空对话
      </el-button>
    </div>

    <!-- 对话区 -->
    <div ref="chatWindow" class="chat-window">
      <div v-if="!messages.length" class="chat-empty">
        <el-icon :size="42" class="empty-icon"><ChatLineSquare /></el-icon>
        <p class="empty-title">试试这样问：</p>
        <div class="empty-examples">
          <div class="example-chip" @click="fillExample('水稻叶片被卷成白色虫苞，里面有小虫子，怎么办？')">
            水稻叶片被卷成白色虫苞，里面有小虫子，怎么办？
          </div>
          <div class="example-chip" @click="fillExample('柑橘树叶子上有很多白色小飞虫')">柑橘树叶子上有很多白色小飞虫</div>
          <div class="example-chip" @click="fillExample('苹果树叶子发黄卷曲')">苹果树叶子发黄卷曲</div>
        </div>
      </div>

      <div v-for="(m, i) in messages" :key="i" class="msg-row" :class="m.role">
        <div class="bubble">
          <div v-if="m.role === 'assistant'" class="bubble-head">
            <el-tag :type="modeTagType[m.mode] || 'info'" effect="light" size="small">
              {{ modeLabel[m.mode] || m.mode }}
            </el-tag>
          </div>
          <p class="bubble-text">{{ m.text }}</p>

          <!-- 追问选择题：点击即作为下一轮提问发出 -->
          <div v-if="m.options && m.options.length" class="clarify-options">
            <div v-for="(opt, oi) in m.options" :key="oi" class="clarify-item">
              <div class="clarify-q">{{ oi + 1 }}. {{ opt.q }}</div>
              <div class="clarify-choices">
                <el-button
                  v-for="c in opt.choices"
                  :key="c"
                  size="small"
                  plain
                  :disabled="loading"
                  @click="sendChoice(opt, c)"
                >
                  {{ c }}
                </el-button>
              </div>
            </div>
            <p class="clarify-hint">点击选项即可作为回答继续对话</p>
          </div>

          <!-- 检索来源 -->
          <div v-if="m.sources && m.sources.length" class="sources">
            <div class="sources-toggle" @click="toggleSources(i)">
              <el-icon><component :is="m.showSources ? 'ArrowDown' : 'ArrowRight'" /></el-icon>
              参考来源（{{ m.sources.length }} 条）
            </div>
            <template v-if="m.showSources">
              <div v-if="m.searchQuery && m.searchQuery !== m.rawQuestion" class="search-query">
                检索词：{{ m.searchQuery }}
              </div>
              <div v-for="(s, si) in m.sources" :key="si" class="source-item">
                <div class="source-head">
                  <span class="source-name">{{ s.chinese_name || s.pest_name }}</span>
                  <el-tag size="small" type="info" effect="plain">{{ chunkLabel(s.chunk_type) }}</el-tag>
                  <span class="source-score">匹配度 {{ (s.score * 100).toFixed(1) }}%</span>
                </div>
                <p class="source-content">{{ s.content }}</p>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div v-if="loading" class="msg-row assistant">
        <div class="bubble typing">正在思考…</div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-bar">
      <el-input
        v-model="draft"
        type="textarea"
        :rows="2"
        maxlength="200"
        resize="none"
        placeholder="描述您观察到的症状，Enter 发送 / Shift+Enter 换行"
        @keydown.enter.exact.prevent="handleSend"
      />
      <el-button type="primary" class="send-btn" :loading="loading" @click="handleSend">
        发送
      </el-button>
    </div>

    <div v-if="error" class="error-panel">
      <el-alert :title="error" type="error" show-icon :closable="false" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
import { ChatLineSquare, RefreshLeft, ArrowDown, ArrowRight } from "@element-plus/icons-vue";
import { ask } from "../api/qa";

const messages = ref([]);
const draft = ref("");
const loading = ref(false);
const error = ref("");
const sessionId = ref(null); // 后端生成，续问带回 → 短期记忆
const chatWindow = ref(null);

const modeLabel = {
  confident: "已确认",
  caution: "仅供参考",
  refused: "无法回答",
  fallback: "检索原文",
  clarify: "需要补充信息",
  off_topic: "换个话题",
};

const modeTagType = {
  confident: "success",
  caution: "warning",
  refused: "info",
  fallback: "warning",
  clarify: "warning",
  off_topic: "info",
};

// chunk_type: 1 基础信息 / 2 症状与发生 / 3 防治方法（与语料切分一致）
const chunkLabel = (t) =>
  ({ 1: "基础信息", 2: "症状与发生", 3: "防治方法" }[t] || "语料片段");

const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value) chatWindow.value.scrollTop = chatWindow.value.scrollHeight;
  });
};

const fillExample = (text) => {
  draft.value = text;
};

const toggleSources = (i) => {
  messages.value[i].showSources = !messages.value[i].showSources;
};

// 点选追问选项：拼成「问题：选项」完整短句再发 —— 判断题的「是/否」单字
// 会被后端 min_length 校验拒绝，且完整短句对向量检索更友好
const sendChoice = (opt, choice) => {
  if (!loading.value) {
    draft.value = `${opt.q}：${choice}`;
    handleSend();
  }
};

const resetChat = () => {
  messages.value = [];
  sessionId.value = null;
  error.value = "";
};

const handleSend = async () => {
  const q = draft.value.trim();
  if (!q || loading.value) return;
  draft.value = "";
  error.value = "";
  messages.value.push({ role: "user", text: q });
  scrollToBottom();

  loading.value = true;
  try {
    const res = await ask(q, sessionId.value);
    sessionId.value = res.session_id || sessionId.value;
    messages.value.push({
      role: "assistant",
      text: res.answer,
      mode: res.mode,
      sources: res.sources || [],
      options: res.options || [],
      // 改写后的检索词透出展示（与原问题不同时才显示，演示/调试可见）
      searchQuery: res.search_query || "",
      rawQuestion: q,
      showSources: false,
    });
  } catch (e) {
    error.value = e?.message || "问答服务暂不可用，请稍后再试";
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};
</script>

<style scoped lang="scss">
.qa-page {
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
  padding-bottom: 24px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
  min-height: 480px;

  .page-header {
    margin-bottom: 16px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    animation: fade-up 0.6s var(--ease-out-expo) both;
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 4px;
    }
    .page-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
      margin: 0;
    }
  }

  .chat-window {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    background: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    animation: fade-up 0.6s var(--ease-out-expo) both;
    animation-delay: 0.08s;

    .chat-empty {
      margin: auto;
      text-align: center;
      .empty-icon { color: var(--text-secondary); }
      .empty-title {
        font-size: 13px;
        color: var(--text-secondary);
        margin: 10px 0;
      }
      .empty-examples {
        display: flex;
        flex-direction: column;
        gap: 8px;
        align-items: center;
        .example-chip {
          font-size: 13px;
          color: var(--primary-color);
          background: var(--primary-light);
          border-radius: 16px;
          padding: 6px 16px;
          cursor: pointer;
          transition: transform 0.15s ease;
          &:hover { transform: translateY(-1px); }
        }
      }
    }

    .msg-row {
      display: flex;
      &.user { justify-content: flex-end; }
      &.assistant { justify-content: flex-start; }

      .bubble {
        max-width: 82%;
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 14px;

        .bubble-text {
          margin: 0;
          line-height: 1.8;
          white-space: pre-wrap;
          color: var(--text-primary);
        }
      }

      &.user .bubble {
        background: var(--primary-color);
        color: #fff;
        border-bottom-right-radius: 4px;
        .bubble-text { color: #fff; }
      }

      &.assistant .bubble {
        background: var(--primary-light);
        border: 1px solid var(--border-color);
        border-bottom-left-radius: 4px;

        .bubble-head { margin-bottom: 6px; }

        .clarify-options {
          margin-top: 10px;
          .clarify-item {
            margin-bottom: 10px;
            .clarify-q {
              font-size: 13px;
              font-weight: 600;
              color: var(--text-primary);
              margin-bottom: 6px;
            }
            .clarify-choices {
              display: flex;
              flex-wrap: wrap;
              gap: 6px;

              /* LLM 生成的选项可能较长，允许换行不被撑爆 */
              :deep(.el-button) {
                white-space: normal;
                word-break: break-all;
                height: auto;
                min-height: 24px;
              }
            }
          }
          .clarify-hint {
            font-size: 12px;
            color: var(--text-secondary);
            margin: 4px 0 0;
          }
        }

        .sources {
          margin-top: 10px;
          padding-top: 8px;
          border-top: 1px dashed var(--border-color);

          .search-query {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 6px;
            &::before {
              content: "🔍 ";
            }
          }

          .sources-toggle {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: var(--text-secondary);
            cursor: pointer;
            user-select: none;
            &:hover { color: var(--primary-color); }
          }

          .source-item {
            background: var(--surface);
            border-radius: 8px;
            padding: 8px 10px;
            margin-top: 8px;

            .source-head {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 4px;
              .source-name {
                font-size: 13px;
                font-weight: 600;
                color: var(--text-primary);
              }
              .source-score {
                margin-left: auto;
                font-size: 12px;
                color: var(--text-secondary);
              }
            }
            .source-content {
              font-size: 12px;
              line-height: 1.7;
              color: var(--text-secondary);
              margin: 0;
            }
          }
        }
      }

      .typing {
        color: var(--text-secondary);
        font-size: 13px;
      }
    }
  }

  .input-bar {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    align-items: flex-end;
    animation: fade-up 0.6s var(--ease-out-expo) both;
    animation-delay: 0.12s;

    .send-btn { height: 54px; }
  }

  .error-panel {
    margin-top: 12px;
  }
}
</style>
