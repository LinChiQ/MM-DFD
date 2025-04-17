<template>
  <div class="home-container">
    <!-- 导航栏 -->
    <header class="navbar">
      <div class="container navbar-container">
        <div class="logo-section">
          <el-image :src="logoSrc" alt="Logo" class="logo"></el-image>
          <h1 class="brand-name">MM-DFD</h1>
        </div>
        <div class="nav-links">
          <a href="#hero" class="nav-link">首页</a>
          <a href="#features" class="nav-link">功能</a>
          <a href="#about" class="nav-link">关于我们</a>
          <a href="#contact" class="nav-link">联系我们</a>
        </div>
        <div class="auth-buttons">
          <el-button type="text" class="login-btn" @click="goToLogin">登录</el-button>
          <el-button type="primary" class="register-btn btn-gradient btn-rounded" @click="goToRegister">免费注册</el-button>
        </div>
      </div>
    </header>

    <!-- 英雄区 -->
    <section id="hero" class="hero-section">
      <div class="container hero-container">
        <div class="hero-content">
          <h1 class="hero-title">多模态深度学习社交媒体虚假新闻检测系统</h1>
          <p class="hero-description">
            基于先进的深度学习技术，结合文本、图像等多模态数据，精准识别社交媒体上的虚假新闻，提供专业的真伪鉴别服务
          </p>
          <div class="hero-buttons">
            <el-button type="primary" class="btn-gradient btn-rounded btn-lg" @click="goToRegister">
              <i class="el-icon-s-promotion"></i> 开始免费体验
            </el-button>
            <el-button class="btn-outline btn-rounded btn-lg" @click="scrollToFeatures">
              <i class="el-icon-view"></i> 了解更多
            </el-button>
          </div>
        </div>
        <div class="hero-image">
          <div class="image-placeholder">
            <div class="detection-illustration"></div>
          </div>
        </div>
      </div>
      <div class="hero-background">
        <div class="bg-blob blob-1"></div>
        <div class="bg-blob blob-2"></div>
        <div class="bg-blob blob-3"></div>
      </div>
    </section>

    <!-- 统计数据 -->
    <section class="stats-section">
      <div class="container stats-container">
        <div class="stat-item">
          <div class="stat-number">98.7%</div>
          <div class="stat-label">检测准确率</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">1000+</div>
          <div class="stat-label">每日检测次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">5000+</div>
          <div class="stat-label">注册用户</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">24/7</div>
          <div class="stat-label">全天候服务</div>
        </div>
      </div>
    </section>

    <!-- 功能特点 -->
    <section id="features" class="features-section">
      <div class="container">
        <h2 class="section-title">强大功能<span class="highlight">特性</span></h2>
        <p class="section-subtitle">我们的系统采用最先进的技术，为您提供全方位的虚假新闻检测服务</p>
        
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <i class="el-icon-picture"></i>
            </div>
            <h3 class="feature-title">多模态分析</h3>
            <p class="feature-description">
              同时分析文本、图像等多种信息，全方位评估新闻内容的真实性，提高检测准确率
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="el-icon-cpu"></i>
            </div>
            <h3 class="feature-title">深度学习技术</h3>
            <p class="feature-description">
              采用前沿的深度学习算法，不断学习和适应新的虚假信息传播模式和技术
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="el-icon-lightning"></i>
            </div>
            <h3 class="feature-title">实时检测</h3>
            <p class="feature-description">
              快速响应，在几秒钟内完成新闻检测，及时辨别虚假信息，防止其传播
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="el-icon-data-line"></i>
            </div>
            <h3 class="feature-title">详细分析报告</h3>
            <p class="feature-description">
              提供全面的分析报告，包括可信度评分、可疑内容标记和详细分析解释
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="el-icon-refresh"></i>
            </div>
            <h3 class="feature-title">持续更新</h3>
            <p class="feature-description">
              系统不断学习新的虚假信息模式，更新检测算法，确保始终保持高准确率
            </p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="el-icon-lock"></i>
            </div>
            <h3 class="feature-title">隐私保护</h3>
            <p class="feature-description">
              严格保护用户数据和检测内容的隐私，确保信息安全不被泄露或滥用
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- 关于我们 -->
    <section id="about" class="about-section">
      <div class="container">
        <div class="about-content">
          <div class="about-text">
            <h2 class="section-title">关于<span class="highlight">我们</span></h2>
            <p class="about-description">
              MM-DFD (多模态深度学习虚假新闻检测系统) 是一个专注于识别和防范虚假新闻传播的先进平台。我们的团队由人工智能专家、数据科学家和媒体研究人员组成，致力于创建更可信的信息环境。
            </p>
            <p class="about-description">
              在当今信息爆炸的时代，虚假新闻的快速传播对社会造成了严重影响。我们的使命是通过技术手段帮助用户快速识别虚假信息，提高社会媒体素养，促进健康信息生态系统的形成。
            </p>
            <p class="about-description">
              我们的系统不断学习和进化，适应新的虚假信息传播技术和模式，为用户提供最准确、最及时的检测服务。
            </p>
          </div>
          <div class="about-image">
            <div class="image-placeholder">
              <div class="about-illustration"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 如何使用 -->
    <section class="how-section">
      <div class="container">
        <h2 class="section-title">如何<span class="highlight">使用</span></h2>
        <p class="section-subtitle">简单几步，即可开始使用我们的虚假新闻检测服务</p>
        
        <div class="steps-container">
          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3 class="step-title">注册账号</h3>
              <p class="step-description">
                简单注册，创建您的个人账号，即可访问完整功能
              </p>
            </div>
          </div>
          
          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-content">
              <h3 class="step-title">提交内容</h3>
              <p class="step-description">
                上传需要检测的新闻内容，包括文本、图片等多媒体资料
              </p>
            </div>
          </div>
          
          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3 class="step-title">获取结果</h3>
              <p class="step-description">
                系统快速分析并生成详细的检测报告，帮助您判断真伪
              </p>
            </div>
          </div>
          
          <div class="step-item">
            <div class="step-number">4</div>
            <div class="step-content">
              <h3 class="step-title">查看历史</h3>
              <p class="step-description">
                随时查看您的检测历史记录，便于追踪和管理
              </p>
            </div>
          </div>
        </div>
        
        <div class="cta-container">
          <el-button type="primary" class="btn-gradient btn-rounded btn-lg" @click="goToRegister">
            立即开始使用
          </el-button>
        </div>
      </div>
    </section>

    <!-- 联系我们 -->
    <section id="contact" class="contact-section">
      <div class="container">
        <h2 class="section-title">联系<span class="highlight">我们</span></h2>
        <p class="section-subtitle">如有任何问题或建议，请随时与我们联系</p>
        
        <div class="contact-info">
          <div class="contact-card">
            <div class="contact-icon">
              <i class="el-icon-message"></i>
            </div>
            <h3 class="contact-title">电子邮件</h3>
            <p class="contact-detail">contact@mm-dfd.com</p>
          </div>
          
          <div class="contact-card">
            <div class="contact-icon">
              <i class="el-icon-phone"></i>
            </div>
            <h3 class="contact-title">电话</h3>
            <p class="contact-detail">+86 123 4567 8910</p>
          </div>
          
          <div class="contact-card">
            <div class="contact-icon">
              <i class="el-icon-location"></i>
            </div>
            <h3 class="contact-title">地址</h3>
            <p class="contact-detail">北京市海淀区学院路100号</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-logo">
            <el-image :src="logoSrc" alt="Logo" class="footer-logo-img"></el-image>
            <span class="footer-brand">MM-DFD</span>
          </div>
          
          <div class="footer-links">
            <div class="footer-links-column">
              <h3 class="footer-links-title">产品</h3>
              <a href="#features" class="footer-link">功能</a>
              <a href="#" class="footer-link">价格</a>
              <a href="#" class="footer-link">API</a>
            </div>
            
            <div class="footer-links-column">
              <h3 class="footer-links-title">资源</h3>
              <a href="#" class="footer-link">文档</a>
              <a href="#" class="footer-link">博客</a>
              <a href="#" class="footer-link">常见问题</a>
            </div>
            
            <div class="footer-links-column">
              <h3 class="footer-links-title">公司</h3>
              <a href="#about" class="footer-link">关于我们</a>
              <a href="#contact" class="footer-link">联系我们</a>
              <a href="#" class="footer-link">加入我们</a>
            </div>
            
            <div class="footer-links-column">
              <h3 class="footer-links-title">法律</h3>
              <a href="#" class="footer-link">隐私政策</a>
              <a href="#" class="footer-link">服务条款</a>
            </div>
          </div>
        </div>
        
        <div class="footer-bottom">
          <p class="copyright">© 2025 MM-DFD (多模态深度学习虚假新闻检测系统). 保留所有权利。</p>
          <div class="social-links">
            <a href="#" class="social-link">
              <i class="el-icon-s-platform"></i>
            </a>
            <a href="#" class="social-link">
              <i class="el-icon-s-marketing"></i>
            </a>
            <a href="#" class="social-link">
              <i class="el-icon-s-promotion"></i>
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'HomePage',
  data() {
    return {
      
    }
  },
  computed: {
    logoSrc() {
      try {
        return require('@/assets/logo.svg')
      } catch (e) {
        return ''
      }
    }
  },
  methods: {
    goToLogin() {
      this.$router.push('/login')
    },
    goToRegister() {
      this.$router.push('/register')
    },
    scrollToFeatures() {
      const featuresSection = document.getElementById('features')
      if (featuresSection) {
        featuresSection.scrollIntoView({ behavior: 'smooth' })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

/* 全局样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.section-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 20px;
  text-align: center;
  color: $main-font-color;
  
  .highlight {
    color: $primary-color;
    position: relative;
    
    &::after {
      content: '';
      position: absolute;
      bottom: 5px;
      left: 0;
      width: 100%;
      height: 8px;
      background-color: rgba($primary-color, 0.2);
      z-index: -1;
    }
  }
}

.section-subtitle {
  font-size: 18px;
  line-height: 1.6;
  text-align: center;
  color: $secondary-font-color;
  max-width: 700px;
  margin: 0 auto 60px;
}

/* 导航栏 */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background-color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
  z-index: 100;
  backdrop-filter: blur(10px);
  padding: 10px 0;
}

.navbar-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
}

.logo {
  width: 40px;
  height: 40px;
}

.brand-name {
  margin: 0 0 0 10px;
  font-size: 24px;
  font-weight: 700;
  color: $main-font-color;
}

.nav-links {
  display: flex;
  gap: 30px;
}

.nav-link {
  color: $regular-font-color;
  text-decoration: none;
  font-weight: 500;
  font-size: 16px;
  transition: $transition-base;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 0;
    height: 2px;
    background-color: $primary-color;
    transition: $transition-base;
  }
  
  &:hover {
    color: $primary-color;
    
    &::after {
      width: 100%;
    }
  }
}

.auth-buttons {
  display: flex;
  align-items: center;
  gap: 15px;
}

.login-btn {
  color: $primary-color;
  font-weight: 500;
  
  &:hover {
    color: darken($primary-color, 10%);
  }
}

.register-btn {
  padding: 10px 20px;
}

/* 英雄区 */
.hero-section {
  padding: 160px 0 100px;
  position: relative;
  overflow: hidden;
}

.hero-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 60px;
}

.hero-content {
  flex: 1;
  max-width: 600px;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 24px;
  color: $main-font-color;
  animation: fadeInUp 0.8s ease-out;
}

.hero-description {
  font-size: 18px;
  line-height: 1.6;
  color: $secondary-font-color;
  margin-bottom: 40px;
  animation: fadeInUp 1s ease-out;
}

.hero-buttons {
  display: flex;
  gap: 20px;
  animation: fadeInUp 1.2s ease-out;
}

.hero-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: fadeIn 1.2s ease-out;
}

.image-placeholder {
  width: 100%;
  height: 400px;
  position: relative;
}

.detection-illustration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url('data:image/svg+xml;base64,PHN2ZyBpZD0iYjY1ODhjYTUtNjIzYy00YjJlLTljOGEtODVkYzRkMGM2ZGJmIiBkYXRhLW5hbWU9IkxheWVyIDEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9Ijg4NS45MzQ3MyIgaGVpZ2h0PSI1OTAuMDAwMDEiIHZpZXdCb3g9IjAgMCA4ODUuOTM0NzMgNTkwLjAwMDAxIj48cGF0aCBkPSJNOTk1LjExOTQxLDY5NWwtLjk5OTc0LjAwMDMxVjI5NGExOTYuMDAwNDMsMTk2LjAwMDQzLDAsMCwwLTE5Ni0xOTZIMzA4LjExOTQxYTE5Ni4wMDA0MywxOTYuMDAwNDMsMCwwLDAtMTk2LDE5NnYyNzZhMTk2LjAwMDQyLDE5Ni4wMDA0MiwwLDAsMCwxOTYsMTk2aDQ5MVYWPSI+PC9wYXRoPjxwYXRoIGQ9Ik01MDEuNzE0NTUsNDYzLjQ0NTVjLTY0LjAwODczLDAtMTE2LjExNzc2LTUyLjEwOTM3LTExNi4xMTc3Ni0xMTYuMTE4MTFzNTIuMTA5LTExNi4xMTc3NiwxMTYuMTE3NzYtMTE2LjExNzc2UzYxNy44MzIzMSwyODMuMzE4NjYsNjE3LjgzMjMxLDM0Ny4zMjczOSw1NjUuNzIzMjgsNDYzLjQ0NTUsNTAxLjcxNDU1LDQ2My40NDU1Wm0wLTIwMi4xMTc3NmMtNDcuNDM2LDAtODYuMTE3NzYsMzguNjgxNzYtODYuMTE3NzYsODYuMTE3NzUsMCw0Ny40MzY1MiwzOC42ODE3Niw4Ni4xMTgxMSw4Ni4xMTc3Niw4Ni4xMTgxMXM4Ni4xMTc3Ni0zOC42ODE1OSw4Ni4xMTc3Ni04Ni4xMTgxMUM1ODcuODMyMzEsMzAwLjAwOTUsNTQ5LjE1MDU1LDI2MS4zMjc3NCw1MDEuNzE0NTUsMjYxLjMyNzc0WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTE1Ny4wMzI2MyAtMTU1KSIgZmlsbD0iIzJiMmQ0MiI+PC9wYXRoPjxjaXJjbGUgY3g9IjM0NC42ODE5MyIgY3k9IjE5Mi4zMjczOSIgcj0iMTUiIGZpbGw9IiM0MzYxZWUiPjwvY2lyY2xlPjxjaXJjbGUgY3g9IjM0NC42ODE5MyIgY3k9IjE5Mi4zMjczOSIgcj0iMTUiIGZpbGw9IiM0MzYxZWUiPjwvY2lyY2xlPjwvc3ZnPg==');
  background-size: cover;
  background-position: center;
  border-radius: $border-radius-large;
  box-shadow: $box-shadow-base;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba($primary-color, 0.3), rgba($info-color, 0.3));
    border-radius: $border-radius-large;
  }
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
}

.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.1;
}

.blob-1 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, $primary-color, $info-color);
  top: -200px;
  right: -100px;
  animation: float 20s infinite alternate ease-in-out;
}

.blob-2 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, $success-color, $info-color);
  bottom: -300px;
  left: -200px;
  animation: float 25s infinite alternate-reverse ease-in-out;
}

.blob-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, $warning-color, $primary-color);
  top: 40%;
  left: 40%;
  animation: float 15s infinite alternate ease-in-out;
}

/* 统计数据 */
.stats-section {
  padding: 60px 0;
  background-color: #fff;
  box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.03);
}

.stats-container {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 30px;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-number {
  font-size: 48px;
  font-weight: 700;
  color: $primary-color;
  margin-bottom: 10px;
  background: linear-gradient(135deg, $primary-color, $info-color);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 18px;
  color: $regular-font-color;
  font-weight: 500;
}

/* 功能特点 */
.features-section {
  padding: 100px 0;
  background-color: $background-color;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  margin-top: 60px;
}

.feature-card {
  background-color: white;
  border-radius: $border-radius-large;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  transition: $transition-base;
  
  &:hover {
    transform: translateY(-10px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
  }
}

.feature-icon {
  font-size: 40px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba($primary-color, 0.1), rgba($info-color, 0.1));
  border-radius: 20px;
  margin-bottom: 20px;
  color: $primary-color;
}

.feature-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 15px;
  color: $main-font-color;
}

.feature-description {
  color: $regular-font-color;
  line-height: 1.6;
}

/* 关于我们 */
.about-section {
  padding: 100px 0;
}

.about-content {
  display: flex;
  align-items: center;
  gap: 60px;
}

.about-text {
  flex: 1;
}

.about-description {
  margin-bottom: 20px;
  color: $regular-font-color;
  font-size: 16px;
  line-height: 1.8;
}

.about-image {
  flex: 1;
}

.about-illustration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url('data:image/svg+xml;base64,PHN2ZyBpZD0iZTU1Y2QxOTUtYmI5ZC00ODI2LWFlNDktNzVlMzZkYTQ1ZTk3IiBkYXRhLW5hbWU9IkxheWVyIDEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9Ijg5My42Mjg4MSIgaGVpZ2h0PSI3NDcuMTI2MjYiIHZpZXdCb3g9IjAgMCA4OTMuNjI4ODEgNzQ3LjEyNjI2Ij48cGF0aCBkPSJNMzg5Ljc3OTEyLDI2MC41OTg5NGMtMzQuNjYyOTQsMC03Mi45NTI4LDEuMzY4OS0xMTMuODY1NzgsNC4wOTk2MS0yMC44OTk5LDEuMzk0NTMtNDIuMTU3MjYsMy4xMjQ5MS02My4yMTE2Myw1LjE1MjM5LTM5LjUxOTc0LDMuODA0LTc2Ljg0MzczLDguMzg3NDUtMTExLjA4MTQyLDEzLjYzNDgtNS40OTgwNS44NDIyOS0xMS4wMjc4MywxLjcxMzg3LTE2LjQ3MDIxLDIuNjA3NDJhMTU1MS4wMjk2MywxNTUxLjAyOTYzLDAsMCwwLTE1Ny42OTQ3MywzMy43OTE3NmwtNC44OTY3MiwxLjI0OC45NzkzNSw3LjkyMzg5YTQ0MS4xNDcwOSw0NDEuMTQ3MDksMCwwLDAsNjguNjQ0ODQsMTgyLjgwNTY3bDEuMzgxODQsMi4yNDY1OCwyLjYxNjIxLS43NjUxM2E1ODMuNDIzNCw1ODMuNDIzNCwwLDAsMSw4MS4wMzgtMTcuOTQ1MzFsLjI4LTIuNjA3NGMzLjAxNzU4LTI4LjAwNDUsMTUuNTM3NTktNTkuODg0NzYsMzUuMjE3NzQtODkuODI5MzUsMTYuMDcyMjctMjQuMzkyNTgsMzMuNjY4NDUtNDQuMDcwMzcsNDkuMzE0LTU5LjE3OTJsMTAuMzcyLTkuNDkyMTktLjA1NjE1LS42MTc2NGMtMS4yNzY2MS0xNC4wMTM2Nyw1LjExNjctMjcuOTIwOSwxOS44NTgyLTQ0LjU0NTlDMjE3LjYzMjI1LDIzOS45MDYsODM2LjAwMDczLDI2MC41OTg5NCwzODkuNzc5MTIsMjYwLjU5ODk0WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTE1My4xODU1OSAtNzYuNDM2ODcpIiBmaWxsPSIjZjJmMmYyIj48L3BhdGg+PHBhdGggZD0iTTE4Ni44NDY0NSwzMzIuNjM4MzVjNDYuODg5LTM3LjExMzgxLDE0MC44MDUzLTI4LjY0OTMsMjA2LjU0MzY3LTIwLjE3NDhDNDY0LjcxNywzMjIuNTQzNDksNTM2LjMzOTcyLDM0MS41NjY3MSw2MTAuMTAxLDM0MS41NjY3MVYzMzkuNTE3QzUzNi43MzUsMzM5LjUxNyw0NjUuNDQsNzYuNDM2ODcsMTUzLjE4NTU5LDc2LjQzNjg3WiIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTE1My4xODU1OSAtNzYuNDM2ODcpIiBmaWxsPSIjNDM2MWVlIj48L3BhdGg+PHBhdGggZD0iTTQ5OC4zNzM1Miw1NDYuMTI0MDdhODcuMjQ1Nyw4Ny4yNDU3LDAsMCwxLTM2LjU4ODA3LDE3LjM5MzMxLDE5Ljg4Mjg1LDE5Ljg4Mjg1LDAsMCwxLTUuNjE2MDcuMDM5MTUsMTAuNjQ0MSwxMC42NDQxLDAsMCwxLTguNDAzLTUuNzgyNzksMTYuMDQzNzQsMTYuMDQzNzQsMCwwLDEtLjkyMTQ5LTEzLjAyMzcxYzIuNjAyLTguODk2NDgsMTAuNjY2ODUtMTUuOTE3MjQsMTguNDk5NzYtMjAuNzMxNzNhNzcuMDAxNDksNzcuMDAxNDksMCwwLDEsMzQuODE1NjctOS43NzgxYzUuMzU3NTItLjM5Mjc0LDExLjQ5MDUuOTA3NjksMTMuMjk0Nyw1Ljk2OTY5YTkuNTMyMTMsOS41MzIxMywwLDAsMS0xLjA1NTg1LDguNjc0MSwxNi41ODM0OSwxNi41ODM0OSwwLDAsMS03LjcyMTgxLDUuNzQzMDZaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtMTUzLjE4NTU5IC03Ni40MzY4NykiIGZpbGw9IiNmYmJlYmUiPjwvcGF0aD48cGF0aCBkPSJNNDYwLjAxNjMzLDU3OC45OTM0N2EzOS4zNDUzNCwzOS4zNDUzNCwwLDAsMCwyLjQ2OTc3LTUuNzM4MjZsMTUuNzcyNy0xLjY5OTE0LTEyLjc2MzcxLTguNDUzLDEwLjk2NDExLTEzLjA3MjQ0LTU4LjY0MjA3LDcuMzg0MzFhMjcuMDM5NTUsMjcuMDM5NTUsMCwwLDAtMTMuMjMwMjEsMTEuNDEwNDVsLjIzNTQ1LS43ODUxNWEyNC40NTgzNCwyNC40NTgzNCwwLDAsMC00LjE1OTg4LDEzLjMyNTQxYy0uMTQ0NDksNC43NDk1MywxLjMzMDkyLDkuNjEwNTYsNC40MDQ2MSwxMy4xNDI3MWEyOC4zOTgsMjguMzk4LDAsMCwwLDkuMTAxMDksNi4yNTk4MmM3LjYyMzI3LDMuMjE0NTgsMTYuMDkxNTYsNS4yMjY3NCwyNC4yNzkzLDUuNzY0Myw0LjAzNjg2LjM2NjU2LDguMzg1NTMuNDA3ODcsMTEuOTAwOTEtMS43MzE5NHMyLjA2MjgzLTUuOTc2ODUtLjU2NDQ5LTcuOTc0NDRhMTIuMzE4NjMsMTIuMzE4NjMsMCwwLDAtMi43NDItMS4yMjg3M2MtMTAuMTM4MjctMy40Mjk2LTIwLjUyODQ4LTcuNTExMzQtMjguNzE2NTYtMTQuNTExNzJhMzUuMTMzNDcsMzUuMTMzNDcsMCwwLDEtNy42MDA5MS04LjYyMDU1LDM4LjAxNDYzLDM4LjAxNDYzLDAsMCwxLTMuMDIzLTYuNDQ3MTkiIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xNTMuMTg1NTkgLTc2LjQzNjg3KSIgZmlsbD0iIzJiMmQ0MiI+PC9wYXRoPjwvc3ZnPg==');
  background-size: cover;
  background-position: center;
  border-radius: $border-radius-large;
  box-shadow: $box-shadow-base;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba($info-color, 0.3), rgba($primary-color, 0.3));
    border-radius: $border-radius-large;
  }
}

/* 如何使用 */
.how-section {
  padding: 100px 0;
  background-color: $background-color;
}

.steps-container {
  max-width: 800px;
  margin: 60px auto;
}

.step-item {
  display: flex;
  gap: 30px;
  align-items: flex-start;
  margin-bottom: 50px;
  position: relative;
  
  &:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 80px;
    left: 30px;
    width: 2px;
    height: calc(100% - 30px);
    background-color: rgba($primary-color, 0.2);
  }
}

.step-number {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, $primary-color, $info-color);
  color: white;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 20px rgba($primary-color, 0.3);
  z-index: 1;
}

.step-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 10px;
  color: $main-font-color;
}

.step-description {
  color: $regular-font-color;
  line-height: 1.6;
}

.cta-container {
  text-align: center;
  margin-top: 60px;
}

/* 联系我们 */
.contact-section {
  padding: 100px 0;
}

.contact-info {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 30px;
  margin-top: 60px;
}

.contact-card {
  background-color: white;
  border-radius: $border-radius-large;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  text-align: center;
  flex: 1;
  min-width: 250px;
  max-width: 300px;
  transition: $transition-base;
  
  &:hover {
    transform: translateY(-10px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
  }
}

.contact-icon {
  font-size: 30px;
  color: $primary-color;
  margin-bottom: 20px;
}

.contact-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 15px;
  color: $main-font-color;
}

.contact-detail {
  color: $regular-font-color;
  line-height: 1.6;
}

/* 页脚 */
.footer {
  background-color: #2b2d42;
  color: white;
  padding: 80px 0 30px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 60px;
  margin-bottom: 60px;
}

.footer-logo {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.footer-logo-img {
  width: 40px;
  height: 40px;
}

.footer-brand {
  font-size: 24px;
  font-weight: 700;
  margin-left: 10px;
}

.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 60px;
}

.footer-links-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: white;
}

.footer-link {
  display: block;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  margin-bottom: 10px;
  transition: $transition-base;
  
  &:hover {
    color: white;
  }
}

.footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.copyright {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.social-links {
  display: flex;
  gap: 15px;
}

.social-link {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  text-decoration: none;
  transition: $transition-base;
  
  &:hover {
    background-color: $primary-color;
    transform: translateY(-3px);
  }
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float {
  0% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(30px, -30px);
  }
  100% {
    transform: translate(0, 0);
  }
}

/* 响应式 */
@media (max-width: $lg) {
  .hero-container {
    flex-direction: column;
  }
  
  .hero-content {
    text-align: center;
    max-width: 100%;
  }
  
  .hero-buttons {
    justify-content: center;
  }
  
  .image-placeholder {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .about-content {
    flex-direction: column-reverse;
  }
  
  .section-title {
    font-size: 32px;
  }
  
  .hero-title {
    font-size: 36px;
  }
}

@media (max-width: $md) {
  .navbar-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .nav-links {
    gap: 15px;
  }
  
  .features-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
  
  .footer-content {
    flex-direction: column;
    gap: 40px;
  }
  
  .footer-links {
    gap: 30px;
  }
  
  .footer-bottom {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: $sm) {
  .hero-section {
    padding: 120px 0 60px;
  }
  
  .nav-links {
    flex-direction: column;
    align-items: center;
  }
  
  .auth-buttons {
    flex-direction: column;
    width: 100%;
  }
}
</style> 