
"""
Wiggly Letters

Copyright (c) 2023 Paul Hindt

This software may be distributed, free of charge, with no strings attached.

The author is not to be held responsible for any damages incurred by the usage of this software.
"""

import array
import sys

import pygame
from pygame.locals import *
import moderngl

SCR_WIDTH = 1920
SCR_HEIGHT = 1080
SCR_WIDTH_HALF = SCR_WIDTH / 2
SCR_HEIGHT_HALF = SCR_HEIGHT / 2

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

VERTEX_ARRAY = [
    # position (x, y), uv coords (x, y)
    -1.0, 1.0, 0.0, 0.0,
    1.0, 1.0, 1.0, 0.0,
    -1.0, -1.0, 0.0, 1.0,
    1.0, -1.0, 1.0, 1.0,
]

VERTEX_SHADER = """
#version 330 core

in vec2 vert;
in vec2 texcoord;
out vec2 uv;

uniform vec2 iMouse;
uniform vec2 iResolution;

void main() {
    uv = texcoord;
    vec2 translate = (iMouse-(iResolution*vec2(0.5))) / iResolution; //(iMouse-(iResolution*vec2(0.5, 0.5)) / iResolution;
    translate.x = -translate.x;
    vec2 v = vert - translate;
    gl_Position = vec4(v, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core

uniform sampler2D iChannel0;
uniform float iTime;

in vec2 uv;
out vec4 fragColor;

void main() {
    //fragColor = vec4(texture(iChannel0, uv).rgb, 1.0);
    float time = iTime * 0.025;
    vec2 center = clamp(vec2(sin(1.0 + time), cos(1.0 + time)), vec2(0.0), vec2(1.0));
    vec2 coord = uv;
    vec2 centered_coord = 2.0 * uv - 1.0;
    float shutter = 0.25;
    float texelDist = distance(center, centered_coord);
    float dist = shutter - texelDist;
    float ripples = 1.0 - sin(texelDist*clamp(8.0 - iTime, 0.0, 8.0) - iTime*0.5);
    coord -= normalize(centered_coord-center)*ripples*0.0050;
    vec4 colorWarp = texture(iChannel0, coord);
    vec4 color = texture(iChannel0, uv);
    vec3 warped = color.rgb * dot(color.rgb, colorWarp.rgb);
    warped = mix(warped, colorWarp.rgb, smoothstep(ripples, ripples + dist, dist));
    fragColor = vec4(warped.rgb, colorWarp.g - iTime);
}
"""
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF) # fullscreen
    display = pygame.Surface((SCR_WIDTH, SCR_HEIGHT))
    clock = pygame.time.Clock()
    font_size = int(SCR_HEIGHT * 0.8)
    font = pygame.font.SysFont("Tahoma", font_size)
    # screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT))
    pygame.display.set_caption("Keyboard Input")
    pygame.mouse.set_pos(SCR_WIDTH_HALF, SCR_HEIGHT_HALF)
    pygame.mouse.set_visible(False)

    ctx = moderngl.create_context()
    ctx.enable(moderngl.BLEND)

    quad_buffer = ctx.buffer(data=array.array('f', VERTEX_ARRAY))
    program = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
    vao = ctx.vertex_array(program, [(quad_buffer, "2f 2f", "vert", "texcoord")])

    tex = ctx.texture(display.get_size(), 4)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    tex.swizzle = "BGRA"

    key = ""
    keys = {}
    last_key = 0
    t = 1.0
    done = False
    frame_num = 0
    while not done:
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    done = True
                else:
                    if event.key not in keys:
                        keys[event.key] = { "key": event.key, "upper": True }

                    key_state = keys[event.key]

                    display.fill(BLACK)

                    if event.key == 32:
                        continue

                    if event.key == last_key:
                        key_state["upper"] = not key_state["upper"]
                        t = 1.0
                    else:
                        t = 1.0
                    if key_state["upper"]:
                        key = pygame.key.name(event.key).upper()
                    else:
                        key = pygame.key.name(event.key).lower()

                    print(f"event.key: {event.key} key: {key} last: {last_key}")

                    last_key = event.key

        # Render the letter on the screen
        text_surface = font.render(key, True, WHITE)
        text_rect = text_surface.get_rect(center=(SCR_WIDTH / 2, SCR_HEIGHT / 2))
        display.blit(text_surface, text_rect)

        tex.write(display.get_view("1"))
        tex.use(0)
        program["iChannel0"] = 0
        program["iTime"] = float(t)
        program["iMouse"] = (mx, my)
        program["iResolution"] = (float(SCR_WIDTH), float(SCR_HEIGHT))
        # ctx.screen.clear(color=(0.0, 0.0, 0.0, 1.0))
        vao.render(mode=moderngl.TRIANGLE_STRIP)

        pygame.display.flip()

        t -= 0.1
        dt = float(clock.tick(60))
        frame_num += 1

    tex.release()
    pygame.quit()

    print("goodbye! -_~")
    sys.exit(0)
