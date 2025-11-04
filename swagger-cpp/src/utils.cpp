#include "utils.hpp"

namespace swagger {

WorldCoord pixel_to_world(
    const NodeId& pixel,
    double resolution,
    double x_offset,
    double y_offset
) {
    WorldCoord world;
    world.x = pixel.second * resolution + x_offset;
    world.y = pixel.first * resolution + y_offset;
    world.z = 0.0;
    return world;
}

NodeId world_to_pixel(
    const WorldCoord& world,
    double resolution,
    double x_offset,
    double y_offset
) {
    int col = static_cast<int>((world.x - x_offset) / resolution);
    int row = static_cast<int>((world.y - y_offset) / resolution);
    return NodeId(row, col);
}

} // namespace swagger
