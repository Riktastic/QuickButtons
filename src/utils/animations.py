"""Animation utilities for QuickButtons application."""

import tkinter as tk
import math
import time
from typing import Callable, Optional, Dict, Any

# Import logger with fallback
try:
    from .logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ButtonAnimator:
    """Handles various button press animations."""
    
    def __init__(self):
        self.active_animations: Dict[tk.Widget, Dict[str, Any]] = {}
    
    def ripple_effect(self, button: tk.Widget, event_x: int, event_y: int, 
                     duration: int = 300, color: str = "#ffffff", opacity: float = 0.3):
        """Create a ripple effect from the click point."""
        try:
            logger.debug(f"Starting ripple effect at ({event_x}, {event_y})")
            
            # Get button dimensions and position
            btn_width = button.winfo_width()
            btn_height = button.winfo_height()
            
            logger.debug(f"Button dimensions: {btn_width}x{btn_height}")
            
            # Create overlay canvas for ripple using button's background color
            button_bg = button.cget("bg")
            overlay = tk.Canvas(button, width=btn_width, height=btn_height, 
                              bg=button_bg, highlightthickness=0, relief='flat')
            overlay.place(x=0, y=0)
            
            # Calculate ripple center relative to button
            center_x = event_x
            center_y = event_y
            
            # Create ripple circle with more visible color
            max_radius = max(btn_width, btn_height) * 0.8
            ripple = overlay.create_oval(
                center_x - 2, center_y - 2, center_x + 2, center_y + 2,
                fill=color, outline=color, width=2, stipple='gray50'
            )
            
            logger.debug(f"Created ripple circle at ({center_x}, {center_y}) with max radius {max_radius}")
            
            # Animation variables
            start_time = time.time()
            start_radius = 2
            end_radius = max_radius
            
            def animate_ripple():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                # Easing function (ease-out)
                eased_progress = 1 - (1 - progress) ** 3
                
                # Calculate current radius and opacity
                current_radius = start_radius + (end_radius - start_radius) * eased_progress
                current_opacity = opacity * (1 - progress)
                
                # Update ripple
                overlay.coords(ripple,
                             center_x - current_radius, center_y - current_radius,
                             center_x + current_radius, center_y + current_radius)
                
                # Update opacity using stipple and outline
                if current_opacity > 0.1:
                    overlay.itemconfig(ripple, stipple='gray50', outline=color)
                else:
                    overlay.itemconfig(ripple, stipple='gray75', outline='')
                
                logger.debug(f"Ripple animation progress: {progress:.2f}, radius: {current_radius:.1f}")
                
                if progress < 1.0:
                    overlay.after(16, animate_ripple)  # ~60 FPS
                else:
                    logger.debug("Ripple animation completed")
                    overlay.destroy()
            
            animate_ripple()
            
        except Exception as e:
            logger.warning(f"Ripple animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def scale_effect(self, button: tk.Widget, duration: int = 150, scale_factor: float = 0.95):
        """Create a scale-down effect on button press."""
        try:
            logger.debug(f"Starting scale effect")
            
            # Store original dimensions
            if not hasattr(button, '_original_width'):
                button._original_width = button.winfo_width()
                button._original_height = button.winfo_height()
            
            start_time = time.time()
            original_scale = 1.0
            target_scale = scale_factor
            
            def animate_scale():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                # Easing function (ease-out)
                eased_progress = 1 - (1 - progress) ** 2
                
                # Calculate current scale
                current_scale = original_scale + (target_scale - original_scale) * eased_progress
                
                # Apply scale transformation
                new_width = int(button._original_width * current_scale)
                new_height = int(button._original_height * current_scale)
                
                # Center the scaled button
                x_offset = (button._original_width - new_width) // 2
                y_offset = (button._original_height - new_height) // 2
                
                button.place_configure(width=new_width, height=new_height, 
                                     x=x_offset, y=y_offset)
                
                if progress < 1.0:
                    button.after(16, animate_scale)
                else:
                    # Restore original size
                    self._restore_button_size(button)
            
            animate_scale()
            
        except Exception as e:
            logger.warning(f"Scale animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def glow_effect(self, button: tk.Widget, duration: int = 200, 
                   glow_color: str = "#4CAF50", intensity: float = 0.6):
        """Create a glow effect on button press."""
        try:
            logger.debug(f"Starting glow effect")
            
            # Store original background
            original_bg = button.cget("bg")
            
            # Calculate glow color
            glow_bg = self._blend_colors(original_bg, glow_color, intensity)
            
            start_time = time.time()
            
            def animate_glow():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                # Sine wave for pulsing effect
                pulse = math.sin(progress * math.pi * 2) * 0.5 + 0.5
                current_intensity = intensity * pulse
                
                # Apply glow
                current_glow = self._blend_colors(original_bg, glow_color, current_intensity)
                button.config(bg=current_glow)
                
                if progress < 1.0:
                    button.after(16, animate_glow)
                else:
                    # Restore original background
                    button.config(bg=original_bg)
            
            animate_glow()
            
        except Exception as e:
            logger.warning(f"Glow animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def bounce_effect(self, button: tk.Widget, duration: int = 300, bounce_height: int = 5):
        """Create a bounce effect on button press."""
        try:
            logger.debug(f"Starting bounce effect")
            
            # Store original position
            if not hasattr(button, '_original_y'):
                button._original_y = button.winfo_y()
            
            start_time = time.time()
            
            def animate_bounce():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                # Bounce function: y = -4x(x-1) for 0 <= x <= 1
                bounce_factor = -4 * progress * (progress - 1)
                current_offset = int(bounce_height * bounce_factor)
                
                # Apply bounce
                button.place_configure(y=button._original_y + current_offset)
                
                if progress < 1.0:
                    button.after(16, animate_bounce)
                else:
                    # Restore original position
                    button.place_configure(y=button._original_y)
            
            animate_bounce()
            
        except Exception as e:
            logger.warning(f"Bounce animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def shake_effect(self, button: tk.Widget, duration: int = 400, shake_intensity: int = 3):
        """Create a shake effect on button press."""
        try:
            logger.debug(f"Starting shake effect")
            
            # Store original position
            if not hasattr(button, '_original_x'):
                button._original_x = button.winfo_x()
            
            start_time = time.time()
            
            def animate_shake():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                # Shake function: damped sine wave
                frequency = 15  # Hz
                damping = 1 - progress
                shake_offset = int(shake_intensity * damping * 
                                 math.sin(frequency * progress * math.pi))
                
                # Apply shake
                button.place_configure(x=button._original_x + shake_offset)
                
                if progress < 1.0:
                    button.after(16, animate_shake)
                else:
                    # Restore original position
                    button.place_configure(x=button._original_x)
            
            animate_shake()
            
        except Exception as e:
            logger.warning(f"Shake animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def flame_effect(self, button: tk.Widget, duration: int = 800):
        """Create a spectacular flame burst effect on button press."""
        try:
            logger.debug(f"Starting flame effect")
            
            # Get button dimensions and position
            btn_width = button.winfo_width()
            btn_height = button.winfo_height()
            
            # Create overlay canvas for flames using button's background color
            button_bg = button.cget("bg")
            overlay = tk.Canvas(button, width=btn_width, height=btn_height, 
                              bg=button_bg, highlightthickness=0, relief='flat')
            overlay.place(x=0, y=0)
            
            # Create multiple flame particles
            flames = []
            num_flames = 12
            
            for i in range(num_flames):
                # Random starting position around button center
                angle = (i / num_flames) * 2 * math.pi
                start_x = btn_width // 2 + math.cos(angle) * 5
                start_y = btn_height // 2 + math.sin(angle) * 5
                
                # Random flame properties
                flame_size = 3 + (i % 3) * 2
                flame_color = ["#FF4500", "#FF6347", "#FF8C00", "#FFD700"][i % 4]
                
                flame = overlay.create_oval(
                    start_x - flame_size, start_y - flame_size,
                    start_x + flame_size, start_y + flame_size,
                    fill=flame_color, outline='', tags=f"flame_{i}"
                )
                flames.append({
                    'id': flame,
                    'start_x': start_x,
                    'start_y': start_y,
                    'angle': angle,
                    'size': flame_size,
                    'color': flame_color,
                    'speed': 2 + (i % 3) * 1.5,
                    'fade_start': 0.3 + (i % 4) * 0.1
                })
            
            start_time = time.time()
            
            def animate_flames():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                for flame_data in flames:
                    flame_id = flame_data['id']
                    
                    # Calculate flame movement (spiral outward)
                    angle = flame_data['angle'] + progress * 2 * math.pi
                    distance = flame_data['speed'] * progress * 50
                    
                    # Add some wobble
                    wobble = math.sin(progress * 20 + flame_data['angle']) * 3
                    
                    x = flame_data['start_x'] + math.cos(angle) * distance + wobble
                    y = flame_data['start_y'] + math.sin(angle) * distance + wobble
                    
                    # Fade out effect
                    if progress > flame_data['fade_start']:
                        fade_progress = (progress - flame_data['fade_start']) / (1 - flame_data['fade_start'])
                        alpha = 1 - fade_progress
                    else:
                        alpha = 1
                    
                    # Update flame position and opacity
                    size = flame_data['size'] * (1 + progress * 0.5)
                    overlay.coords(flame_id, x - size, y - size, x + size, y + size)
                    
                    # Change color as flame progresses
                    if progress < 0.3:
                        color = flame_data['color']
                    elif progress < 0.7:
                        color = "#FFD700"  # Golden
                    else:
                        color = "#FFA500"  # Orange
                    
                    overlay.itemconfig(flame_id, fill=color)
                
                if progress < 1.0:
                    overlay.after(16, animate_flames)
                else:
                    overlay.destroy()
            
            animate_flames()
            
        except Exception as e:
            logger.warning(f"Flame animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def confetti_effect(self, button: tk.Widget, duration: int = 1500):
        """Create a spectacular confetti burst effect on button press."""
        try:
            logger.debug(f"Starting confetti effect")
            
            # Get button dimensions and position
            btn_width = button.winfo_width()
            btn_height = button.winfo_height()
            
            logger.debug(f"Button dimensions: {btn_width}x{btn_height}")
            
            # Ensure button has valid dimensions
            if btn_width <= 0 or btn_height <= 0:
                logger.warning(f"Invalid button dimensions: {btn_width}x{btn_height}")
                btn_width = max(btn_width, 50)
                btn_height = max(btn_height, 30)
                logger.debug(f"Using fallback dimensions: {btn_width}x{btn_height}")
            
            # Create overlay canvas for confetti using button's background color
            button_bg = button.cget("bg")
            overlay = tk.Canvas(button, width=btn_width, height=btn_height, 
                              bg=button_bg, highlightthickness=0, relief='flat')
            overlay.place(x=0, y=0)
            
            logger.debug(f"Created confetti overlay canvas at (0,0) with size {btn_width}x{btn_height}")
            
            # Create confetti particles
            confetti_pieces = []
            num_pieces = 20  # Reduced from 25
            
            confetti_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
                             "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"]
            
            logger.debug(f"Creating {num_pieces} confetti pieces")
            
            for i in range(num_pieces):
                # Random starting position at button center
                start_x = btn_width // 2 + (i % 5 - 2) * 3  # Reduced spacing
                start_y = btn_height // 2 + (i // 5 - 2) * 3  # Reduced spacing
                
                # Ensure position is within button bounds
                start_x = max(5, min(start_x, btn_width - 5))
                start_y = max(5, min(start_y, btn_height - 5))
                
                # Random confetti properties
                piece_type = i % 3  # 0=circle, 1=square, 2=triangle
                color = confetti_colors[i % len(confetti_colors)]
                size = 2 + (i % 4)  # Made pieces smaller (was 4 + i % 6)
                angle = (i / num_pieces) * 2 * math.pi
                speed = 2 + (i % 3) * 1.5  # Reduced speed
                
                if piece_type == 0:  # Circle
                    piece = overlay.create_oval(
                        start_x - size, start_y - size,
                        start_x + size, start_y + size,
                        fill=color, outline=color, width=1, tags=f"confetti_{i}"
                    )
                elif piece_type == 1:  # Square
                    piece = overlay.create_rectangle(
                        start_x - size, start_y - size,
                        start_x + size, start_y + size,
                        fill=color, outline=color, width=1, tags=f"confetti_{i}"
                    )
                else:  # Triangle
                    points = [
                        start_x, start_y - size,
                        start_x - size, start_y + size,
                        start_x + size, start_y + size
                    ]
                    piece = overlay.create_polygon(
                        points, fill=color, outline=color, width=1, tags=f"confetti_{i}"
                    )
                
                logger.debug(f"Created confetti piece {i}: type={piece_type}, color={color}, size={size}, pos=({start_x},{start_y})")
                
                confetti_pieces.append({
                    'id': piece,
                    'start_x': start_x,
                    'start_y': start_y,
                    'angle': angle,
                    'speed': speed,
                    'size': size,
                    'color': color,
                    'type': piece_type,
                    'rotation': 0,
                    'gravity': 0.2 + (i % 3) * 0.1  # Reduced gravity
                })
            
            logger.debug(f"Created {len(confetti_pieces)} confetti pieces")
            start_time = time.time()
            
            def animate_confetti():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                logger.debug(f"Confetti animation progress: {progress:.2f}")
                
                for piece_data in confetti_pieces:
                    piece_id = piece_data['id']
                    
                    # Calculate confetti movement (burst outward with gravity)
                    angle = piece_data['angle'] + progress * 0.5
                    distance = piece_data['speed'] * progress * 40  # Reduced distance
                    
                    # Add gravity effect
                    gravity_offset = piece_data['gravity'] * progress * progress * 20  # Reduced gravity effect
                    
                    x = piece_data['start_x'] + math.cos(angle) * distance
                    y = piece_data['start_y'] + math.sin(angle) * distance + gravity_offset
                    
                    # Rotation effect
                    piece_data['rotation'] += 3  # Reduced rotation speed
                    
                    # Fade out effect
                    if progress > 0.7:
                        fade_progress = (progress - 0.7) / 0.3
                        alpha = 1 - fade_progress
                    else:
                        alpha = 1
                    
                    # Update confetti position and rotation based on type
                    size = piece_data['size']
                    try:
                        if piece_data['type'] == 0:  # Circle - just update position
                            overlay.coords(piece_id, x - size, y - size, x + size, y + size)
                        elif piece_data['type'] == 1:  # Square - just update position (no rotation for rectangles)
                            overlay.coords(piece_id, x - size, y - size, x + size, y + size)
                        else:  # Triangle - update with rotation
                            angle_rad = piece_data['rotation'] * math.pi / 180
                            cos_a = math.cos(angle_rad)
                            sin_a = math.sin(angle_rad)
                            
                            # Create rotated triangle points (6 coordinates for polygon)
                            points = [
                                x, y - size,  # top point
                                x - size, y + size,  # bottom left
                                x + size, y + size   # bottom right
                            ]
                            
                            # Apply rotation to each point
                            rotated_points = []
                            for j in range(0, len(points), 2):
                                px, py = points[j], points[j+1]
                                rx = x + (px - x) * cos_a - (py - y) * sin_a
                                ry = y + (px - x) * sin_a + (py - y) * cos_a
                                rotated_points.extend([rx, ry])
                            
                            overlay.coords(piece_id, *rotated_points)
                    except Exception as coord_error:
                        logger.warning(f"Error updating confetti piece {piece_data['type']}: {coord_error}")
                        # Fallback: just update position without rotation
                        overlay.coords(piece_id, x - size, y - size, x + size, y + size)
                
                if progress < 1.0:
                    overlay.after(16, animate_confetti)
                else:
                    logger.debug("Confetti animation completed")
                    overlay.destroy()
            
            logger.debug("Starting confetti animation")
            animate_confetti()
            
        except Exception as e:
            logger.warning(f"Confetti animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def sparkle_effect(self, button: tk.Widget, duration: int = 600):
        """Create a magical sparkle effect on button press."""
        try:
            logger.debug(f"Starting sparkle effect")
            
            # Get button dimensions and position
            btn_width = button.winfo_width()
            btn_height = button.winfo_height()
            
            # Create overlay canvas for sparkles using button's background color
            button_bg = button.cget("bg")
            overlay = tk.Canvas(button, width=btn_width, height=btn_height, 
                              bg=button_bg, highlightthickness=0, relief='flat')
            overlay.place(x=0, y=0)
            
            # Create sparkle particles
            sparkles = []
            num_sparkles = 15
            
            sparkle_colors = ["#FFD700", "#FFA500", "#FF69B4", "#00CED1", "#9370DB"]
            
            for i in range(num_sparkles):
                # Random starting position around button
                start_x = btn_width // 2 + (i % 5 - 2) * 8
                start_y = btn_height // 2 + (i // 5 - 1) * 8
                
                # Random sparkle properties
                color = sparkle_colors[i % len(sparkle_colors)]
                size = 2 + (i % 3)
                angle = (i / num_sparkles) * 2 * math.pi
                speed = 2 + (i % 2) * 1.5
                
                # Create star-shaped sparkle
                points = []
                for j in range(10):
                    point_angle = j * math.pi / 5
                    if j % 2 == 0:
                        radius = size
                    else:
                        radius = size * 0.5
                    x = start_x + math.cos(point_angle) * radius
                    y = start_y + math.sin(point_angle) * radius
                    points.extend([x, y])
                
                sparkle = overlay.create_polygon(
                    points, fill=color, outline='', tags=f"sparkle_{i}"
                )
                
                sparkles.append({
                    'id': sparkle,
                    'start_x': start_x,
                    'start_y': start_y,
                    'angle': angle,
                    'speed': speed,
                    'size': size,
                    'color': color,
                    'rotation': 0,
                    'pulse_phase': i * 0.5
                })
            
            start_time = time.time()
            
            def animate_sparkles():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                for sparkle_data in sparkles:
                    sparkle_id = sparkle_data['id']
                    
                    # Calculate sparkle movement (spiral outward)
                    angle = sparkle_data['angle'] + progress * 1.5 * math.pi
                    distance = sparkle_data['speed'] * progress * 40
                    
                    x = sparkle_data['start_x'] + math.cos(angle) * distance
                    y = sparkle_data['start_y'] + math.sin(angle) * distance
                    
                    # Rotation and pulsing effect
                    sparkle_data['rotation'] += 8
                    pulse = math.sin(progress * 10 + sparkle_data['pulse_phase']) * 0.3 + 1
                    
                    # Fade out effect
                    if progress > 0.6:
                        fade_progress = (progress - 0.6) / 0.4
                        alpha = 1 - fade_progress
                    else:
                        alpha = 1
                    
                    # Update sparkle position and size
                    size = sparkle_data['size'] * pulse
                    points = []
                    for j in range(10):
                        point_angle = j * math.pi / 5 + sparkle_data['rotation'] * math.pi / 180
                        if j % 2 == 0:
                            radius = size
                        else:
                            radius = size * 0.5
                        px = x + math.cos(point_angle) * radius
                        py = y + math.sin(point_angle) * radius
                        points.extend([px, py])
                    
                    overlay.coords(sparkle_id, *points)
                    
                    # Change color intensity
                    if progress < 0.3:
                        color = sparkle_data['color']
                    elif progress < 0.7:
                        color = "#FFD700"  # Golden
                    else:
                        color = "#FFA500"  # Orange
                    
                    overlay.itemconfig(sparkle_id, fill=color)
                
                if progress < 1.0:
                    overlay.after(16, animate_sparkles)
                else:
                    overlay.destroy()
            
            animate_sparkles()
            
        except Exception as e:
            logger.warning(f"Sparkle animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def explosion_effect(self, button: tk.Widget, duration: int = 900):
        """Create a spectacular explosion effect on button press."""
        try:
            logger.debug(f"Starting explosion effect")
            
            # Get button dimensions and position
            btn_width = button.winfo_width()
            btn_height = button.winfo_height()
            
            # Create overlay canvas for explosion using button's background color
            button_bg = button.cget("bg")
            overlay = tk.Canvas(button, width=btn_width, height=btn_height, 
                              bg=button_bg, highlightthickness=0, relief='flat')
            overlay.place(x=0, y=0)
            
            # Create explosion particles
            particles = []
            num_particles = 20
            
            explosion_colors = ["#FF4500", "#FF6347", "#FF8C00", "#FFD700", "#FFA500"]
            
            for i in range(num_particles):
                # Random starting position at button center
                start_x = btn_width // 2
                start_y = btn_height // 2
                
                # Random particle properties
                angle = (i / num_particles) * 2 * math.pi + (i % 3) * 0.2
                color = explosion_colors[i % len(explosion_colors)]
                size = 3 + (i % 4) * 2
                speed = 4 + (i % 3) * 2
                
                # Create particle (circle)
                particle = overlay.create_oval(
                    start_x - size, start_y - size,
                    start_x + size, start_y + size,
                    fill=color, outline='', tags=f"particle_{i}"
                )
                
                particles.append({
                    'id': particle,
                    'start_x': start_x,
                    'start_y': start_y,
                    'angle': angle,
                    'speed': speed,
                    'size': size,
                    'color': color,
                    'trail_length': 3 + (i % 3)
                })
            
            start_time = time.time()
            
            def animate_explosion():
                current_time = time.time()
                elapsed = current_time - start_time
                progress = min(elapsed / (duration / 1000), 1.0)
                
                for particle_data in particles:
                    particle_id = particle_data['id']
                    
                    # Calculate particle movement (explosion outward)
                    angle = particle_data['angle']
                    distance = particle_data['speed'] * progress * 80
                    
                    # Add some randomness to the explosion
                    wobble = math.sin(progress * 15 + particle_data['angle']) * 5
                    
                    x = particle_data['start_x'] + math.cos(angle) * distance + wobble
                    y = particle_data['start_y'] + math.sin(angle) * distance + wobble
                    
                    # Size variation
                    size_variation = 1 + math.sin(progress * 20) * 0.3
                    current_size = particle_data['size'] * size_variation
                    
                    # Fade out effect
                    if progress > 0.5:
                        fade_progress = (progress - 0.5) / 0.5
                        alpha = 1 - fade_progress
                    else:
                        alpha = 1
                    
                    # Update particle position and size
                    overlay.coords(particle_id, 
                                 x - current_size, y - current_size,
                                 x + current_size, y + current_size)
                    
                    # Change color as explosion progresses
                    if progress < 0.2:
                        color = particle_data['color']
                    elif progress < 0.5:
                        color = "#FFD700"  # Golden
                    elif progress < 0.8:
                        color = "#FFA500"  # Orange
                    else:
                        color = "#FF6347"  # Tomato
                    
                    overlay.itemconfig(particle_id, fill=color)
                
                if progress < 1.0:
                    overlay.after(16, animate_explosion)
                else:
                    overlay.destroy()
            
            animate_explosion()
            
        except Exception as e:
            logger.warning(f"Explosion animation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _restore_button_size(self, button: tk.Widget):
        """Restore button to original size."""
        try:
            if hasattr(button, '_original_width') and hasattr(button, '_original_height'):
                button.place_configure(width=button._original_width, 
                                     height=button._original_height, x=0, y=0)
        except Exception as e:
            logger.warning(f"Failed to restore button size: {e}")
    
    def _blend_colors(self, color1: str, color2: str, factor: float) -> str:
        """Blend two hex colors by the given factor (0-1)."""
        try:
            # Remove # if present
            color1 = color1.lstrip('#')
            color2 = color2.lstrip('#')
            
            # Convert to RGB
            r1, g1, b1 = tuple(int(color1[i:i+2], 16) for i in (0, 2, 4))
            r2, g2, b2 = tuple(int(color2[i:i+2], 16) for i in (0, 2, 4))
            
            # Blend
            r = int(r1 + (r2 - r1) * factor)
            g = int(g1 + (g2 - g1) * factor)
            b = int(b1 + (b2 - b1) * factor)
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return color1  # Return original color if blending fails


# Global animator instance
animator = ButtonAnimator()


def animate_button_press(button: tk.Widget, event_x: int = None, event_y: int = None, 
                        animation_type: str = "ripple", **kwargs):
    """Apply animation to button press.
    
    Args:
        button: The button widget to animate
        event_x: X coordinate of click (for ripple effect)
        event_y: Y coordinate of click (for ripple effect)
        animation_type: Type of animation ("ripple", "scale", "glow", "bounce", "shake", "flame", "confetti", "sparkle", "explosion")
        **kwargs: Additional animation parameters
    """
    try:
        logger.debug(f"Starting animation: {animation_type}")
        
        if animation_type == "ripple":
            animator.ripple_effect(button, event_x or button.winfo_width()//2, 
                                 event_y or button.winfo_height()//2, **kwargs)
        elif animation_type == "scale":
            animator.scale_effect(button, **kwargs)
        elif animation_type == "glow":
            animator.glow_effect(button, **kwargs)
        elif animation_type == "bounce":
            animator.bounce_effect(button, **kwargs)
        elif animation_type == "shake":
            animator.shake_effect(button, **kwargs)
        elif animation_type == "flame":
            animator.flame_effect(button, **kwargs)
        elif animation_type == "confetti":
            animator.confetti_effect(button, **kwargs)
        elif animation_type == "sparkle":
            animator.sparkle_effect(button, **kwargs)
        elif animation_type == "explosion":
            animator.explosion_effect(button, **kwargs)
        elif animation_type == "combined":
            # Apply multiple effects
            animator.scale_effect(button, duration=150, **kwargs)
            animator.glow_effect(button, duration=200, **kwargs)
        else:
            logger.warning(f"Unknown animation type: {animation_type}")
    except Exception as e:
        logger.warning(f"Button animation failed: {e}")
        import traceback
        traceback.print_exc()


def get_available_animations() -> list:
    """Get list of available animation types."""
    return ["ripple", "scale", "glow", "bounce", "shake", "flame", "confetti", "sparkle", "explosion", "combined"]


def get_animation_defaults() -> dict:
    """Get default parameters for each animation type."""
    return {
        "ripple": {"duration": 300, "color": "#ffffff", "opacity": 0.3},
        "scale": {"duration": 150, "scale_factor": 0.95},
        "glow": {"duration": 200, "glow_color": "#4CAF50", "intensity": 0.6},
        "bounce": {"duration": 300, "bounce_height": 5},
        "shake": {"duration": 400, "shake_intensity": 7},
        "flame": {"duration": 800},
        "confetti": {"duration": 1000},
        "sparkle": {"duration": 600},
        "explosion": {"duration": 900},
        "combined": {"duration": 200, "scale_factor": 0.95, "glow_color": "#4CAF50", "intensity": 0.6}
    } 