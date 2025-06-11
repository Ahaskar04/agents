# demomanim_simple.py - No LaTeX required version
from manim import *
import numpy as np

class ProjectileMotion(Scene):
    def construct(self):
        # Scene settings
        self.camera.background_color = "#1a1a2e"
        
        # Title
        title = Text("Projectile Motion", font_size=48, color=BLUE_B)
        subtitle = Text("v₀ = 20 m/s", font_size=24, color=GRAY_B)
        subtitle.next_to(title, DOWN)
        title_group = VGroup(title, subtitle)
        
        self.play(Write(title), Write(subtitle))
        self.wait(2)  # NARRATION POINT 1
        
        self.play(FadeOut(title_group))
        
        # Create ground
        ground = Line(LEFT * 6, RIGHT * 6, color=GREEN).shift(DOWN * 3)
        ground_label = Text("Ground", font_size=16, color=GREEN).next_to(ground, DOWN)
        
        self.play(Create(ground), Write(ground_label))
        self.wait(1)  # NARRATION POINT 2
        
        # Create ball
        ball = Dot(radius=0.3, color=BLUE, z_index=5)
        ball.move_to(LEFT * 4 + DOWN * 2.7)
        
        # Initial velocity arrow
        velocity_arrow = Arrow(
            start=ball.get_center(),
            end=ball.get_center() + UP * 2 + RIGHT * 0.5,
            color=YELLOW,
            buff=0.3
        )
        v_label = Text("v₀ = 20 m/s", font_size=20, color=YELLOW)
        v_label.next_to(velocity_arrow, RIGHT)
        
        self.play(
            FadeIn(ball),
            Create(velocity_arrow),
            Write(v_label)
        )
        self.wait(2)  # NARRATION POINT 3
        
        # Remove velocity indicators
        self.play(FadeOut(velocity_arrow), FadeOut(v_label))
        
        # Create path (parabola)
        def projectile_path(t):
            x = -4 + 4 * t  # Horizontal motion
            y = -2.7 + 8 * t - 4.9 * t**2  # Vertical motion with gravity
            return np.array([x, y, 0])
        
        # Calculate time to hit ground again
        t_max = 8 / (2 * 4.9)  # Time at maximum height
        
        # Create the path
        path = ParametricFunction(
            projectile_path,
            t_range=[0, 2 * t_max],
            color=WHITE,
            stroke_width=2
        )
        
        # Animate the throw
        self.play(
            MoveAlongPath(ball, path),
            Create(path),
            run_time=4,
            rate_func=linear
        )
        self.wait(1)  # NARRATION POINT 4
        
        # Show maximum height
        max_height_line = DashedLine(
            start=DOWN * 2.7,
            end=projectile_path(t_max),
            color=RED,
            dash_length=0.1
        )
        
        height_brace = Brace(max_height_line, RIGHT, color=RED)
        height_text = Text("h = 20.4 m", font_size=24, color=RED)
        height_text.next_to(height_brace, RIGHT)
        
        # Move ball to maximum height
        self.play(ball.animate.move_to(projectile_path(t_max)))
        self.play(
            Create(max_height_line),
            GrowFromCenter(height_brace),
            Write(height_text)
        )
        self.wait(2)  # NARRATION POINT 5
        
        # Show velocity components
        v_y_arrow = Arrow(
            start=ball.get_center(),
            end=ball.get_center() + DOWN * 0.5,
            color=ORANGE,
            buff=0
        )
        v_y_label = Text("vy = 0", font_size=16, color=ORANGE)
        v_y_label.next_to(v_y_arrow, RIGHT)
        
        self.play(Create(v_y_arrow), Write(v_y_label))
        self.wait(2)  # NARRATION POINT 6
        
        # Clean up velocity indicators
        self.play(FadeOut(v_y_arrow), FadeOut(v_y_label))
        
        # Show the equation using Text instead of MathTex
        equation_line1 = Text("Maximum height formula:", font_size=28, color=YELLOW)
        equation_line2 = Text("h = v₀² / (2g)", font_size=32, color=WHITE)
        equation_line3 = Text("h = 20² / (2 × 9.8) = 20.4 m", font_size=28, color=WHITE)
        
        equation_group = VGroup(equation_line1, equation_line2, equation_line3)
        equation_group.arrange(DOWN, buff=0.3)
        equation_group.to_edge(UP)
        
        self.play(Write(equation_line1))
        self.play(Write(equation_line2))
        self.play(Write(equation_line3))
        self.wait(3)  # NARRATION POINT 7
        
        # Final message
        self.play(
            FadeOut(equation_group),
            FadeOut(max_height_line),
            FadeOut(height_brace),
            FadeOut(height_text)
        )
        
        conclusion = Text(
            "Projectile motion combines horizontal\nand vertical motion independently",
            font_size=32,
            color=BLUE_B
        )
        conclusion.move_to(UP * 2)
        
        self.play(Write(conclusion))
        self.wait(3)  # NARRATION POINT 8
        
        # Fade out everything
        self.play(*[FadeOut(mob) for mob in self.mobjects])