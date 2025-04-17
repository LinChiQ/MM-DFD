<template>
  <div class="not-found-container">
    <div class="background-decoration"></div>
    <div class="not-found-content">
      <div class="not-found-icon">404</div>
      <h2>页面不存在</h2>
      <p>抱歉，您访问的页面不存在或已被移除</p>
      <el-button type="primary" class="home-button" @click="goHome">
        <i class="el-icon-s-home"></i> 返回首页
      </el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotFound',
  methods: {
    goHome() {
      this.$router.push('/')
    }
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.not-found-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: relative;
  overflow: hidden;
}

.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 10% 20%, rgba($primary-color, 0.03) 0%, transparent 20%),
    radial-gradient(circle at 90% 80%, rgba($primary-color, 0.03) 0%, transparent 20%),
    radial-gradient(circle at 50% 50%, rgba($primary-color, 0.06) 0%, transparent 30%),
    radial-gradient(circle at 80% 10%, rgba($info-color, 0.04) 0%, transparent 20%);
  z-index: 0;
}

.not-found-content {
  text-align: center;
  padding: 60px;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: $border-radius-large;
  box-shadow: $box-shadow-base;
  max-width: 500px;
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.6s ease-out;
  backdrop-filter: blur(10px);
}

.not-found-icon {
  font-size: 120px;
  font-weight: 800;
  background: linear-gradient(135deg, $primary-color, $info-color);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 20px;
  line-height: 1;
  animation: pulse 3s infinite;
  text-shadow: 0 10px 30px rgba($primary-color, 0.2);
}

h2 {
  margin: 20px 0;
  color: $main-font-color;
  font-size: 28px;
  font-weight: 600;
}

p {
  margin-bottom: 30px;
  color: $regular-font-color;
  font-size: 16px;
  line-height: 1.6;
}

.home-button {
  height: 48px;
  padding: 0 30px;
  font-size: 16px;
  font-weight: 500;
  border-radius: $border-radius-base;
  background: linear-gradient(90deg, $primary-color, $info-color);
  border: none;
  transition: transform 0.3s, box-shadow 0.3s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba($primary-color, 0.4);
  }
  
  i {
    margin-right: 8px;
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

@keyframes pulse {
  0% {
    text-shadow: 0 5px 20px rgba($primary-color, 0.2);
  }
  50% {
    text-shadow: 0 5px 30px rgba($primary-color, 0.5);
  }
  100% {
    text-shadow: 0 5px 20px rgba($primary-color, 0.2);
  }
}

@media (max-width: $sm) {
  .not-found-content {
    padding: 40px 20px;
    max-width: 90%;
  }
  
  .not-found-icon {
    font-size: 100px;
  }
  
  h2 {
    font-size: 24px;
  }
}
</style> 