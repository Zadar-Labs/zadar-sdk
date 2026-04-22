uint32 cluster_id
uint32 frame_num
uint32 subframe_index
bool is_static

float32 x
float32 y
float32 z

float64 doppler
float64 snr
float64 noise

float32 d_min
float32 d_max
float32 r_min
float32 r_max
float32 lambda1
float32 lambda2
float32 lambda3

uint32 num_points

geometry_msgs/Point32[] vertices
sensor_msgs/PointCloud2 scan
