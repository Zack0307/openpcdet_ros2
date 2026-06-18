# openpcdet_ros2 套件說明

## 這是什麼

這是一個 **ROS 2（ament_python 架構）套件**，名為 `openpcdet_ros2`。實際內容是一套**搭載 Yahboom Rosmaster 控制板的四輪/Ackermann 轉向小車**的 ROS 2 驅動與 PS4 搖桿遙控程式，外加 Gazebo 模擬用的機器人模型（URDF）與感測器（光達、相機、IMU）描述檔。


## 主要功能

1. **PS4 搖桿遙控小車**
   - `joy_to_twist.py`（執行檔名 `ps4_turtle`）：訂閱 `/joy` 搖桿訊號，換算成 `Twist` 速度指令，並透過 `Rosmaster_Lib` 直接控制小車的伺服轉向與電子變速（ESC），同時持續發布 IMU、磁力計、電壓等感測器資料。
   - `ps4.py`（執行檔名 `ps4`）：較精簡的版本，只把 `/joy` 轉成 `/turtle1/cmd_vel`，不直接控制硬體，較像是單純的測試/示範節點。

2. **Rosmaster 硬體介接層**
   - `Rosmaster_Lib.py`：透過序列埠（UART）與 Yahboom Rosmaster 控制板通訊的完整協定實作，支援讀取 IMU/陀螺儀/磁力計、電池電壓、編碼器，以及下發馬達轉速、舵機角度、蜂鳴器、RGB 燈效、機械手臂控制等指令（支援 X3 / X3 Plus / X1 / R2 多種車型）。

3. **機器人模型與模擬（Gazebo / RViz）**
   - `urdf/` 下的 xacro 檔組合出一台具備光達、相機、深度相機的機器人模型，並有對應的 Gazebo 感測器外掛設定（`mobile_base_gazebo.xacro`、`lidar.xacro` 等）。
   - `rviz/autoware.rviz`、`rviz/rplidar_ros.rviz`：預先配置好的 RViz 視覺化設定，方便直接看光達掃描與機器人狀態。

4. **感測融合與定位**
   - `param/imu_filter_param.yaml`：給 `imu_filter_madgwick` 套件用的參數，把原始 IMU 數據濾波成姿態估計。
   - 啟動檔中也預留了 `robot_localization`（EKF）節點設定，可把輪速與 IMU 融合成較準確的定位（odometry）。

5. **整合啟動檔**
   - `launch/jetson.launch.py`：設計給 Jetson 上的真實小車使用的啟動腳本，目前實際會啟動的節點是 `ps4_turtle`（小車驅動）與 `joy_node`（讀取搖桿）；RViz、光達、IMU 濾波、EKF 定位等節點都已寫好但先被註解掉，等同於目前是「先求能動再逐步打開其他模組」的狀態。

## 套件目錄結構

```
openpcdet_ros2-main/
├── launch/
│   └── jetson.launch.py        # 主啟動檔（PS4 + 小車驅動）
├── openpcdet_ros2/
│   ├── Rosmaster_Lib.py         # Rosmaster 控制板通訊協定函式庫
│   ├── joy_to_twist.py          # 搖桿 → 小車控制（含硬體控制）
│   ├── ps4.py                   # 搖桿 → cmd_vel（精簡版）
│   └── __init__.py
├── param/
│   └── imu_filter_param.yaml    # IMU 濾波器參數
├── rviz/
│   ├── autoware.rviz
│   └── rplidar_ros.rviz
├── urdf/
│   ├── my_robot.urdf.xacro      # 機器人模型主檔
│   ├── mobile_base.xacro        # 車身/輪子幾何
│   ├── mobile_base_gazebo.xacro # Gazebo 差速驅動外掛
│   ├── camera.xacro             # RGB 相機
│   ├── depth_camera.xacro       # 深度相機
│   ├── lidar.xacro              # 光達 Gazebo 外掛
│   └── common_properties.xacro  # 共用慣性/材質設定
├── test/                        # ament 測試樣板（copyright、flake8、pep257）
├── package.xml
├── setup.py / setup.cfg
└── resource/openpcdet_ros2
```

## 相依套件

由 `package.xml` 與程式碼可看出此套件需要：

- ROS 2（`rclpy`、`sensor_msgs`、`geometry_msgs`、`std_msgs`）
- `robot_localization`（EKF 定位）
- `joy`（讀取搖桿輸入）
- `imu_filter_madgwick`（IMU 濾波，啟動檔中有引用但 package.xml 未列出）
- `rplidar_ros`（光達驅動，啟動檔中有引用但 package.xml 未列出）
- Python 套件 `pyserial`（`Rosmaster_Lib.py` 用 `serial` 與控制板通訊）

## 如何啟動（在已建置好的 ROS 2 workspace 中）

```bash
ros2 launch openpcdet_ros2 jetson.launch.py
```

執行後會啟動搖桿節點與小車驅動節點，插上 PS4 搖桿（需先連接好 `/dev/myserial` 序列埠對應的 Rosmaster 控制板）即可用搖桿控制小車前進、轉向。

## 目前狀態與待補完的部分

- `package.xml` 的 `<description>` 與 `<license>` 都還是預設的 `TODO`，尚未填寫。
- `my_robot.urdf.xacro` 內的 `xacro:include` 路徑是寫死的絕對路徑（`/home/dllab/ros2_ws/...`），換到別的機器或別人的 workspace 會找不到檔案，需要改成用 `$(find openpcdet_ros2)` 或 `get_package_share_directory` 的方式動態取得路徑。
- 啟動檔中光達、RViz、IMU 濾波、EKF 定位、`cartographer`（建圖）等節點都已寫好但被註解掉，要使用時需自行取消註解並確認對應套件已安裝。
