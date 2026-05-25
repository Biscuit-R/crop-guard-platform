<template>
  <div class="dataset-tools-page">
    <div class="page-header">
      <div class="header-top">
        <el-button text @click="$router.push('/tools')">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回高级功能</span>
        </el-button>
      </div>
      <h1 class="page-title">数据集工具</h1>
      <p class="page-desc">通用数据集格式转化工具，支持 XML、VOC、COCO、CSV 格式自动转化为 YOLO 训练格式</p>
    </div>

    <!-- 功能说明卡片 -->
    <el-card class="info-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><InfoFilled /></el-icon>
          <span>功能说明</span>
        </div>
      </template>
      <div class="info-content">
        <div class="info-item">
          <div class="info-icon xml">XML</div>
          <div class="info-text">
            <h4>XML 标注格式</h4>
            <p>适用于 LabelImg 标注的 XML 文件（图片与标注同目录）</p>
          </div>
        </div>
        <div class="info-item">
          <div class="info-icon voc">VOC</div>
          <div class="info-text">
            <h4>Pascal VOC 格式</h4>
            <p>适用于标准 VOC 目录结构（Annotations + JPEGImages）</p>
          </div>
        </div>
        <div class="info-item">
          <div class="info-icon coco">COCO</div>
          <div class="info-text">
            <h4>Microsoft COCO 格式</h4>
            <p>适用于 COCO 数据集及使用 COCO 格式标注的数据</p>
          </div>
        </div>
        <div class="info-item">
          <div class="info-icon csv">CSV</div>
          <div class="info-text">
            <h4>CSV 表格格式</h4>
            <p>适用于使用 CSV 文件记录标注信息的数据集</p>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 转化工具卡片 -->
    <el-card class="convert-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><SetUp /></el-icon>
          <span>格式转化</span>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <!-- 选择格式 -->
        <el-form-item label="输入格式" prop="format">
          <el-radio-group v-model="form.format">
            <el-radio-button value="xml">
              <span class="format-radio-icon">XML</span>
              <span class="format-radio-desc">LabelImg 标注</span>
            </el-radio-button>
            <el-radio-button value="voc">
              <span class="format-radio-icon">VOC</span>
              <span class="format-radio-desc">Pascal VOC</span>
            </el-radio-button>
            <el-radio-button value="coco">
              <span class="format-radio-icon">COCO</span>
              <span class="format-radio-desc">JSON 标注</span>
            </el-radio-button>
            <el-radio-button value="csv">
              <span class="format-radio-icon">CSV</span>
              <span class="format-radio-desc">表格标注</span>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 上传文件 -->
        <el-form-item label="数据集文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".zip"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将 ZIP 压缩包拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                请上传 ZIP 格式的数据集压缩包
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 类别信息 -->
        <el-form-item
          v-if="form.format !== 'coco'"
          label="类别列表"
          prop="classes"
        >
          <el-input
            v-model="form.classes"
            type="textarea"
            :rows="6"
            placeholder="每行一个类别名，按顺序编号（从 0 开始）&#10;例如：&#10;rice_leaf_roller&#10;rice_leaf_caterpillar&#10;paddy_stem_maggot"
          />
          <div class="form-tip">
            <el-icon><QuestionFilled /></el-icon>
            <span>COCO 格式会自动从标注文件中提取类别，无需手动填写</span>
          </div>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
            size="large"
          >
            <el-icon v-if="!loading"><VideoPlay /></el-icon>
            <span>{{ loading ? '转化中...' : '开始转化' }}</span>
          </el-button>
          <el-button @click="handleReset" size="large">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 转化结果 -->
    <el-card v-if="result" class="result-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><CircleCheckFilled /></el-icon>
          <span>转化结果</span>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="转化状态">
          <el-tag type="success" size="large">转化成功</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="转化数量">
          <span class="result-number">{{ result.converted_count }}</span> 张图片
        </el-descriptions-item>
        <el-descriptions-item label="类别数量">
          <span class="result-number">{{ result.classes_count }}</span> 个类别
        </el-descriptions-item>
        <el-descriptions-item label="输入格式">
          <el-tag>{{ form.format.toUpperCase() }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="result-actions">
        <el-button type="primary" size="large" @click="handleDownload">
          <el-icon><Download /></el-icon>
          <span>下载 YOLO 数据集</span>
        </el-button>
      </div>

      <el-alert
        title="后续步骤"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <ol class="result-steps">
            <li>解压下载的 <code>yolo_dataset.zip</code></li>
            <li>将解压后的文件夹放到项目目录</li>
            <li>修改 <code>data.yaml</code> 中的路径</li>
            <li>运行 <code>python train.py --data ./yolo_dataset/data.yaml</code></li>
          </ol>
        </template>
      </el-alert>
    </el-card>

    <!-- 目录结构说明 -->
    <el-card class="structure-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><FolderOpened /></el-icon>
          <span>目录结构说明</span>
        </div>
      </template>

      <div class="structure-grid">
        <div class="structure-item">
          <h4>XML 格式输入</h4>
          <pre class="tree">xml_data/
├── img001.xml
├── img001.jpg
├── img002.xml
└── img002.jpg</pre>
        </div>
        <div class="structure-item">
          <h4>VOC 格式输入</h4>
          <pre class="tree">voc_data/
├── Annotations/
│   ├── img001.xml
│   └── img002.xml
└── JPEGImages/
    ├── img001.jpg
    └── img002.jpg</pre>
        </div>
        <div class="structure-item">
          <h4>COCO 格式输入</h4>
          <pre class="tree">coco_data/
├── annotations.json
└── images/
    ├── img001.jpg
    └── img002.jpg</pre>
        </div>
        <div class="structure-item">
          <h4>CSV 格式输入</h4>
          <pre class="tree">csv_data/
├── labels.csv
└── images/
    ├── img001.jpg
    └── img002.jpg</pre>
        </div>
        <div class="structure-item">
          <h4>YOLO 格式输出</h4>
          <pre class="tree">yolo_dataset/
├── data.yaml
├── images/
│   └── train/
│       ├── img001.jpg
│       └── img002.jpg
└── labels/
    └── train/
        ├── img001.txt
        └── img002.txt</pre>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  InfoFilled,
  SetUp,
  UploadFilled,
  QuestionFilled,
  CircleCheckFilled,
  Download,
  FolderOpened,
  VideoPlay,
  ArrowLeft,
} from "@element-plus/icons-vue";
import { convertDataset, downloadConvertedDataset } from "../api/dataset";
import { useUserStore } from "../stores/user";

const userStore = useUserStore();

const formRef = ref(null);
const uploadRef = ref(null);
const loading = ref(false);
const result = ref(null);

const form = reactive({
  format: "voc",
  file: null,
  classes: "",
});

const rules = {
  format: [{ required: true, message: "请选择输入格式", trigger: "change" }],
  file: [{ required: true, message: "请上传数据集文件", trigger: "change" }],
};

const handleFileChange = (uploadFile) => {
  form.file = uploadFile.raw;
};

const handleFileRemove = () => {
  form.file = null;
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
  } catch {
    return;
  }

  if (!form.file) {
    ElMessage.warning("请上传数据集文件");
    return;
  }

  loading.value = true;
  result.value = null;

  try {
    const res = await convertDataset(form.file, form.format, form.classes);
    result.value = res;
    ElMessage.success("转化成功！");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "转化失败，请检查文件格式");
  } finally {
    loading.value = false;
  }
};

const handleDownload = async () => {
  try {
    const userId = userStore.userInfo?.id;
    if (!userId) {
      ElMessage.error("用户信息获取失败");
      return;
    }

    const res = await downloadConvertedDataset(userId);
    const blob = new Blob([res], { type: "application/zip" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "yolo_dataset.zip";
    link.click();
    window.URL.revokeObjectURL(url);

    ElMessage.success("下载成功！");
  } catch (error) {
    ElMessage.error("下载失败");
  }
};

const handleReset = () => {
  formRef.value?.resetFields();
  form.file = null;
  result.value = null;
  uploadRef.value?.clearFiles();
};
</script>

<style scoped>
.dataset-tools-page {
  max-width: 1040px; margin: 0 auto; padding: 0;
}

.page-header {
  margin-bottom: 24px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
}

.header-top {
  margin-bottom: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.info-card {
  margin-bottom: 24px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.1s;
}

.info-content {
  display: flex;
  gap: 24px;
}

.info-item {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
}

.info-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: white;
  flex-shrink: 0;
}

.info-icon.xml {
  background: #8b5cf6;
}

.info-icon.voc {
  background: #f59e0b;
}

.info-icon.coco {
  background: #3b82f6;
}

.info-icon.csv {
  background: #10b981;
}

.info-text h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.info-text p {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.convert-card {
  margin-bottom: 24px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.2s;
}

.format-radio-icon {
  font-weight: 600;
}

.format-radio-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 4px;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.result-card {
  margin-bottom: 24px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
}

.result-number {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary-color);
}

.result-actions {
  margin: 24px 0;
  text-align: center;
}

.result-steps {
  margin: 0;
  padding-left: 20px;
}

.result-steps li {
  margin-bottom: 4px;
}

.result-steps code {
  background: var(--primary-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.structure-card {
  margin-bottom: 24px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.3s;
}

.structure-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.structure-item {
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
}

.structure-item h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.tree {
  margin: 0;
  font-family: "Monaco", "Menlo", "Consolas", monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
}

:deep(.el-radio-button__inner) {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>
