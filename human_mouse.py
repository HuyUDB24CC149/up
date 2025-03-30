import time
import random
import math
import numpy as np
from bezier import Curve
from scipy.interpolate import splprep, splev
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

class HumanMouse:
    def __init__(self, driver, window_size=(1800, 1080), window_scale=0.35):
        """
        Khởi tạo HumanMouse với driver và thông số cửa sổ
        
        :param driver: WebDriver instance
        :param window_size: Kích thước cửa sổ trình duyệt (width, height)
        :param window_scale: Tỷ lệ thu phóng của cửa sổ
        """
        self.driver = driver
        self.window_size = window_size
        self.window_scale = window_scale
        self.action_chains = ActionChains(driver)
        
    def get_element_center(self, element):
        """Tính tọa độ trung tâm của phần tử"""
        if isinstance(element, str):
            # Nếu element là CSS selector
            element = self.driver.find_element(By.CSS_SELECTOR, element)
            
        location = element.location
        size = element.size
        
        # Tính toán tọa độ trung tâm
        center_x = location['x'] + size['width'] / 2
        center_y = location['y'] + size['height'] / 2
        
        return (center_x, center_y)
    
    def get_current_mouse_position(self):
        """Lấy vị trí hiện tại của chuột"""
        return self.driver.execute_script("""
            return [window.mouseX || window.innerWidth/2, 
                    window.mouseY || window.innerHeight/2];
        """)
    
    def generate_bezier_curve(self, start_point, end_point, control_points=2, randomness=0.4):
        """
        Tạo đường cong Bezier cho chuyển động chuột
        
        :param start_point: Điểm bắt đầu (x, y)
        :param end_point: Điểm kết thúc (x, y)
        :param control_points: Số điểm điều khiển cho đường cong
        :param randomness: Mức độ ngẫu nhiên của đường cong (0-1)
        :return: Danh sách các điểm trên đường cong
        """
        # Tạo list điểm điều khiển
        points = [start_point]
        
        # Tính toán khoảng cách giữa điểm bắt đầu và kết thúc
        distance = math.sqrt((end_point[0] - start_point[0])**2 + (end_point[1] - start_point[1])**2)
        
        # Tính toán số lượng điểm trung gian dựa trên khoảng cách
        num_points = max(10, int(distance / 10))
        
        # Thêm các điểm điều khiển ngẫu nhiên
        for i in range(control_points):
            # Tạo điểm điều khiển với độ ngẫu nhiên
            random_x = (start_point[0] * (1 - (i + 1) / (control_points + 1)) + 
                      end_point[0] * ((i + 1) / (control_points + 1)) + 
                      random.uniform(-distance * randomness, distance * randomness))
            
            random_y = (start_point[1] * (1 - (i + 1) / (control_points + 1)) + 
                      end_point[1] * ((i + 1) / (control_points + 1)) + 
                      random.uniform(-distance * randomness, distance * randomness))
            
            points.append((random_x, random_y))
        
        # Thêm điểm kết thúc
        points.append(end_point)
        
        # Tạo đường cong Bezier
        nodes = np.asfortranarray([
            [p[0] for p in points],
            [p[1] for p in points]
        ])
        
        curve = Curve(nodes, degree=len(points) - 1)
        s_vals = np.linspace(0.0, 1.0, num_points)
        path_points = curve.evaluate_multi(s_vals)
        
        return [(path_points[0][i], path_points[1][i]) for i in range(len(s_vals))]
    
    def add_human_noise_to_path(self, path, noise_amplitude=2.0):
        """
        Thêm độ nhiễu vào đường đi để tăng tính tự nhiên
        
        :param path: Danh sách điểm trên đường đi
        :param noise_amplitude: Biên độ nhiễu
        :return: Danh sách điểm đã thêm nhiễu
        """
        noisy_path = []
        for point in path:
            # Thêm nhiễu ngẫu nhiên vào mỗi điểm
            noise_x = random.uniform(-noise_amplitude, noise_amplitude)
            noise_y = random.uniform(-noise_amplitude, noise_amplitude)
            noisy_path.append((point[0] + noise_x, point[1] + noise_y))
        return noisy_path
    
    def human_move_to_element(self, element, click=False, randomize_final_position=True):
        """
        Di chuyển chuột đến phần tử giống như người thật
        
        :param element: WebElement hoặc CSS selector
        :param click: Có click vào phần tử hay không
        :param randomize_final_position: Tạo độ ngẫu nhiên cho vị trí cuối cùng
        """
        # Lấy vị trí hiện tại của chuột và vị trí phần tử
        start_point = self.get_current_mouse_position()
        target_point = self.get_element_center(element)
        
        # Áp dụng tỷ lệ thu phóng cho điểm đích
        scaled_target_x = target_point[0] * self.window_scale
        scaled_target_y = target_point[1] * self.window_scale
        end_point = (scaled_target_x, scaled_target_y)
        
        # Tính khoảng cách
        distance = math.sqrt((end_point[0] - start_point[0])**2 + (end_point[1] - start_point[1])**2)
        
        # Tạo đường cong Bezier cho chuyển động
        path = self.generate_bezier_curve(
            start_point, 
            end_point, 
            control_points=random.randint(2, 4),
            randomness=random.uniform(0.2, 0.5)
        )
        
        # Thêm độ nhiễu vào đường đi
        path = self.add_human_noise_to_path(path, noise_amplitude=min(3.0, distance * 0.05))
        
        # Di chuyển chuột theo đường đi
        for i, point in enumerate(path):
            # Tính toán khoảng cách giữa các điểm
            if i > 0:
                prev_point = path[i-1]
                point_distance = math.sqrt((point[0] - prev_point[0])**2 + (point[1] - prev_point[1])**2)
                
                # Tính toán thời gian di chuyển dựa trên khoảng cách và vị trí
                # Người dùng thật thường di chuyển nhanh hơn ở giữa và chậm lại ở cuối
                progress = i / len(path)  # Tiến trình từ 0 đến 1
                
                # Tốc độ thay đổi theo dạng hình chuông - nhanh ở giữa, chậm ở đầu và cuối
                speed_factor = 1 - 0.8 * abs(2 * progress - 1)**2
                
                # Tốc độ cơ bản dựa trên khoảng cách tổng thể
                base_speed = 0.3 + distance / 2000
                
                # Thời gian ngủ tùy thuộc vào khoảng cách và tốc độ
                sleep_time = (point_distance / 100) / (base_speed * speed_factor)
                sleep_time = min(0.05, sleep_time)  # Giới hạn tối đa
                
                # Thêm yếu tố ngẫu nhiên vào thời gian ngủ
                sleep_time *= random.uniform(0.8, 1.2)
                
                time.sleep(sleep_time)
            
            # Di chuyển đến điểm hiện tại
            try:
                # Sử dụng JavaScript để di chuyển chuột một cách mượt mà hơn
                self.driver.execute_script(f"""
                    var event = new MouseEvent('mousemove', {{
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': {point[0]},
                        'clientY': {point[1]}
                    }});
                    document.dispatchEvent(event);
                    
                    // Lưu vị trí chuột hiện tại
                    window.mouseX = {point[0]};
                    window.mouseY = {point[1]};
                """)
            except Exception:
                # Fallback nếu JavaScript không hoạt động
                actions = ActionChains(self.driver)
                actions.move_by_offset(point[0] - start_point[0], point[1] - start_point[1])
                actions.perform()
                start_point = point
        
        # Đảm bảo chuột đã đến đúng vị trí mục tiêu
        if isinstance(element, str):
            element = self.driver.find_element(By.CSS_SELECTOR, element)
            
        # Click nếu được yêu cầu
        if click:
            # Ngủ nhẹ trước khi click để giống người thật
            time.sleep(random.uniform(0.05, 0.2))
            
            try:
                # Thử click bằng JavaScript trước
                self.driver.execute_script("arguments[0].click();", element)
            except Exception:
                try:
                    # Thử click bằng ActionChains nếu JavaScript không hoạt động
                    actions = ActionChains(self.driver)
                    actions.click(element)
                    actions.perform()
                except Exception:
                    # Cuối cùng, thử click trực tiếp nếu các cách khác không hoạt động
                    element.click()
            
            # Ngủ sau khi click với thời gian ngẫu nhiên
            time.sleep(random.uniform(0.1, 0.3))