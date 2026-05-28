import cv2
import numpy as np

# ===================== 输入/输出说明（中文）=====================
# 任务：用 OpenCV 的 SIFT 特征 + FLANN 匹配，把当前输入图像
#       识别为“最像的参考图类别（label）”，否则输出 None。
#
# 主要输入（Input）：
# 1) 参考图像：通过 `add_reference_image(image_path, label)` 加入
# 2) 当前帧/待识别图像：通过 `match_image(frame)` 传入（frame 为 BGR 图像）
#
# 主要输出（Output）：
# - `add_reference_image(...)`：返回 bool，表示是否成功加入并提取特征
# - `match_image(frame)`：返回 best_match（字符串 label）或 None
# =================================================================

class ImageRecognitionSystem:
    def __init__(self, similarity_threshold=0.7):
        self.reference_images = {}
        self.reference_features = {}
        self.similarity_threshold = similarity_threshold
        # 创建SIFT检测器
        self.sift = cv2.SIFT_create()
        # 创建FLANN匹配器
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)
        
    def add_reference_image(self, image_path, label):
        # 输入（Input）：
        #   - image_path：参考图路径（png/jpg 等）
        #   - label：这张参考图所属类别名（例如 "video1"）
        # 输出（Output）：
        #   - True：成功加载图片并提取 SIFT descriptors
        #   - False：图片加载失败或提取 descriptors 失败
        try:
            # 读取参考图像
            img = cv2.imread(image_path)
            if img is None:
                print(f"无法加载图像: {image_path}")
                return False
            
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            self.reference_images[label] = gray
            
            # 提取SIFT特征
            keypoints, descriptors = self.sift.detectAndCompute(gray, None)
            if descriptors is not None:
                self.reference_features[label] = (keypoints, descriptors)
                print(f"已添加参考图像: {label}，提取了 {len(keypoints)} 个特征点")
                return True
            else:
                print(f"无法从图像中提取特征: {image_path}")
                return False
        except Exception as e:
            print(f"添加参考图像时出错: {e}")
            return False
    
    def match_image(self, frame):
        # 输入（Input）：
        #   - frame：当前帧图像（BGR，来自 cv2.VideoCapture.read() 的 frame）
        # 输出（Output）：
        #   - label（字符串）：若最匹配的相似度 > similarity_threshold
        #   - None：若最匹配相似度不够，认为没有命中任何类别
        # 将当前帧转换为灰度图
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 提取当前帧的SIFT特征
        frame_keypoints, frame_descriptors = self.sift.detectAndCompute(gray_frame, None)
        
        if frame_descriptors is None:
            print("当前帧无法提取特征")
            return None
        
        best_match = None
        best_match_ratio = 0
        
        # 与所有参考图像进行比较
        for label, (ref_keypoints, ref_descriptors) in self.reference_features.items():
            try:
                # 使用FLANN匹配器进行特征匹配
                matches = self.flann.knnMatch(frame_descriptors, ref_descriptors, k=2)
                
                # 应用比率测试，筛选好的匹配
                good_matches = []
                for m, n in matches:
                    if m.distance < 0.75 * n.distance:
                        good_matches.append(m)
                
                # 计算匹配比率
                match_ratio = len(good_matches) / max(len(frame_keypoints), 1)
                print(f"与 {label} 的匹配比率: {match_ratio:.4f}，好的匹配点: {len(good_matches)}")
                
                # 更新最佳匹配
                if match_ratio > best_match_ratio:
                    best_match_ratio = match_ratio
                    best_match = label
                    
            except Exception as e:
                print(f"匹配图像 {label} 时出错: {e}")
        
        # 如果最佳匹配的相似度高于阈值，返回标签
        if best_match_ratio > self.similarity_threshold:
            print(f"匹配到图像: {best_match}, 匹配比率: {best_match_ratio:.4f}")
            return best_match
        
        return None