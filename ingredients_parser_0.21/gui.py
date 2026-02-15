import tkinter as tk
from tkinter import (
    filedialog,
    Scale,
    Button,
    Label,
    Frame,
    IntVar,
    DoubleVar,
    StringVar,
    Checkbutton,
    messagebox,
)
import cv2
import numpy as np
import os
from PIL import Image, ImageTk
from datetime import datetime


class ImageProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor for OCR Enhancement")
        self.root.geometry("1200x800")

        # Variables for image processing
        self.original_img = None
        self.displayed_img = None
        self.processed_img = None
        self.file_path = None

        # Processing parameters
        self.brightness = IntVar(value=0)
        self.contrast = DoubleVar(value=1.0)
        self.sharpness = DoubleVar(value=0.0)
        self.threshold_method = StringVar(value="adaptive")
        self.threshold_value = IntVar(value=127)
        self.adaptive_block_size = IntVar(value=11)
        self.adaptive_c = IntVar(value=2)
        self.blur_size = IntVar(value=0)
        self.dilate_iterations = IntVar(value=0)
        self.erode_iterations = IntVar(value=0)
        self.invert = IntVar(value=0)

        # Enhanced parameters based on existing code
        self.bilateral_d = IntVar(value=9)
        self.bilateral_sigma_color = IntVar(value=15)
        self.bilateral_sigma_space = IntVar(value=15)
        self.use_bilateral = IntVar(value=0)

        self.use_clahe = IntVar(value=0)
        self.clahe_clip_limit = DoubleVar(value=2.0)
        self.clahe_grid_size = IntVar(value=8)

        self.use_glare_reduction = IntVar(value=0)
        self.glare_threshold = IntVar(value=200)

        self.kernel_size = IntVar(value=2)
        self.use_opening = IntVar(value=0)
        self.use_closing = IntVar(value=0)

        self.use_lab = IntVar(value=0)
        self.l_enhance = IntVar(value=0)

        # Create frames
        self.create_frames()

        # Create widgets
        self.create_widgets()

    def batch_process_directory(self):
        """Process all images in a directory with current settings"""
        if self.processed_img is None:
            messagebox.showinfo(
                "Batch Processing",
                "Please process an image first to establish settings",
            )
            return

        # Ask for source directory
        source_dir = filedialog.askdirectory(title="Select Directory with Images")
        if not source_dir:
            return

        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return

        # Get list of image files
        image_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
        image_files = [
            f
            for f in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, f))
            and f.lower().endswith(image_extensions)
        ]

        if not image_files:
            messagebox.showinfo(
                "Batch Processing", "No image files found in selected directory"
            )
            return

        # Confirm batch processing
        confirm = messagebox.askyesno(
            "Batch Processing",
            f"Found {len(image_files)} images. Process all with current settings?",
        )

        if not confirm:
            return

        # Process each image
        processed_count = 0
        for file in image_files:
            try:
                # Load the image
                img_path = os.path.join(source_dir, file)
                img = cv2.imread(img_path)

                if img is None:
                    continue

                # Store original image
                self.original_img = img

                # Process with current settings
                self.update_preview()

                # Save processed image
                output_path = os.path.join(output_dir, f"processed_{file}")
                cv2.imwrite(output_path, self.processed_img)

                processed_count += 1
            except Exception as e:
                print(f"Error processing {file}: {e}")

        # Show completion message
        messagebox.showinfo(
            "Batch Processing Complete",
            f"Successfully processed {processed_count} out of {len(image_files)} images.\n"
            f"Processed images saved to {output_dir}",
        )

    def analyze_commas_and_dots(self):
        """Analyze the image specifically for comma and dot detection"""
        if self.original_img is None or self.processed_img is None:
            messagebox.showinfo("Analysis", "Please load and process an image first")
            return

        # Make a copy of the processed image for analysis
        analysis_img = self.processed_img.copy()

        # Find contours to identify potential punctuation marks
        contours, _ = cv2.findContours(
            analysis_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter contours based on size (commas and dots are small)
        small_contours = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)

            # Filter by area and dimensions
            # Punctuation marks are typically small and have specific aspect ratios
            if area < 100 and area > 3:  # Adjust these thresholds based on your images
                if w < 10 and h < 10:  # Small size
                    # Dots are roughly square
                    if 0.8 < w / h < 1.2:
                        small_contours.append((contour, "dot"))
                    # Commas are taller than wide
                    elif h / w > 1.2 and h / w < 3:
                        small_contours.append((contour, "comma"))

        # Create a visualization image (convert to color if needed)
        if len(analysis_img.shape) == 2:
            vis_img = cv2.cvtColor(analysis_img, cv2.COLOR_GRAY2BGR)
        else:
            vis_img = analysis_img.copy()

        # Draw the identified punctuation marks
        dot_count = 0
        comma_count = 0

        for contour, punc_type in small_contours:
            if punc_type == "dot":
                # Draw dots in blue
                cv2.drawContours(vis_img, [contour], 0, (255, 0, 0), 2)
                dot_count += 1
            else:
                # Draw commas in green
                cv2.drawContours(vis_img, [contour], 0, (0, 255, 0), 2)
                comma_count += 1

        # Save the visualization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(self.file_path) if self.file_path else "image"
        base_name = os.path.splitext(base_name)[0]

        # Ask for directory to save analysis
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"{base_name}_punctuation_analysis_{timestamp}.png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*"),
            ],
        )

        if save_path:
            cv2.imwrite(save_path, vis_img)

        # Show results
        messagebox.showinfo(
            "Punctuation Analysis",
            f"Analysis complete!\n\nDetected approximately:\n"
            f"- {dot_count} dots/periods\n"
            f"- {comma_count} commas\n\n"
            f"The analyzed image has been saved with detected punctuation highlighted.",
        )

        # Return to display the original processed image
        self.display_image(self.processed_img)

    def create_frames(self):
        # Left frame for controls
        self.control_frame = Frame(self.root, width=300, bg="#f0f0f0", padx=10, pady=10)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Right frame for image display
        self.display_frame = Frame(self.root, bg="#ffffff")
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create menu bar
        self.create_menu()

    def create_menu(self):
        """Create menu bar with additional options"""
        menubar = tk.Menu(self.root)

        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load Image", command=self.load_image)
        filemenu.add_command(label="Save Processed Image", command=self.save_image)
        filemenu.add_command(label="Save All Variants", command=self.save_variants)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # Tools menu
        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(
            label="Analyze Commas and Dots", command=self.analyze_commas_and_dots
        )
        toolsmenu.add_command(
            label="Batch Process Directory", command=self.batch_process_directory
        )
        toolsmenu.add_separator()
        toolsmenu.add_command(
            label="Reset All Parameters", command=self.reset_parameters
        )
        menubar.add_cascade(label="Tools", menu=toolsmenu)

        # Presets menu
        presetmenu = tk.Menu(menubar, tearoff=0)
        presetmenu.add_command(
            label="Punctuation Enhancement", command=self.preset_punctuation
        )
        presetmenu.add_command(
            label="Small Text Enhancement", command=self.preset_small_text
        )
        presetmenu.add_command(label="Glare Reduction", command=self.preset_glare)
        presetmenu.add_command(
            label="Multi-technique OCR Optimization",
            command=self.preset_multi_technique,
        )
        presetmenu.add_separator()
        presetmenu.add_command(
            label="High Contrast Labels", command=self.preset_high_contrast
        )
        presetmenu.add_command(
            label="Low Contrast/Faded Text", command=self.preset_low_contrast
        )
        presetmenu.add_command(
            label="Inverted Text (White on Dark)", command=self.preset_inverted
        )
        menubar.add_cascade(label="Presets", menu=presetmenu)

        # Help menu
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Usage Tips", command=self.show_usage_tips)
        helpmenu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)

    def show_usage_tips(self):
        """Show usage tips dialog"""
        tips = """
        Ingredient Label OCR Enhancement Tips:
        
        1. For detecting commas and dots:
           - Try the "Punctuation Enhancement" or "Small Text Enhancement" presets
           - Use bilateral filtering to preserve small details
           - Smaller adaptive threshold block sizes (7-11) work better for small details
           
        2. For light or faded text:
           - Use CLAHE enhancement
           - Increase contrast (1.5-2.0)
           - Try the "Low Contrast/Faded Text" preset
           
        3. For glare or reflections:
           - Use the "Glare Reduction" preset
           - Enable LAB color space processing
           
        4. For overall best results:
           - Generate all variants with "Save All Variants"
           - Use "Analyze Commas and Dots" to check detection quality
           - Test multiple presets on your specific labels
        """

        messagebox.showinfo("Usage Tips", tips)

    def show_about(self):
        """Show about dialog"""
        about_text = """
        Ingredient Label OCR Image Processor
        
        A specialized tool for enhancing ingredient label images
        for better OCR recognition, with focus on detecting
        commas, dots, and small punctuation marks.
        
        This tool incorporates techniques from PaddleOCR
        preprocessing to optimize text extraction from
        product packaging.
        """

        messagebox.showinfo("About", about_text)

    def create_widgets(self):
        # File controls
        Label(
            self.control_frame,
            text="Image Controls",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
        ).pack(pady=(0, 10))
        Button(self.control_frame, text="Load Image", command=self.load_image).pack(
            fill=tk.X, pady=5
        )
        Button(
            self.control_frame, text="Save Processed Image", command=self.save_image
        ).pack(fill=tk.X, pady=5)
        Button(
            self.control_frame, text="Save All Variants", command=self.save_variants
        ).pack(fill=tk.X, pady=5)

        # Create notebook for tabbed interface
        try:
            from tkinter import ttk

            self.notebook = ttk.Notebook(self.control_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

            # Basic tab
            self.basic_tab = Frame(self.notebook, bg="#f0f0f0", padx=10, pady=10)
            self.notebook.add(self.basic_tab, text="Basic")

            # Advanced tab
            self.advanced_tab = Frame(self.notebook, bg="#f0f0f0", padx=10, pady=10)
            self.notebook.add(self.advanced_tab, text="Advanced")

            # Presets tab
            self.presets_tab = Frame(self.notebook, bg="#f0f0f0", padx=10, pady=10)
            self.notebook.add(self.presets_tab, text="Presets")

            # Create basic controls
            self.create_basic_controls()

            # Create advanced controls
            self.create_advanced_controls()

            # Create presets
            self.create_presets()

        except ImportError:
            # Fall back to basic layout if ttk is not available
            Label(
                self.control_frame,
                text="Processing Parameters",
                font=("Arial", 12, "bold"),
                bg="#f0f0f0",
            ).pack(pady=(20, 10))
            self.create_basic_controls_fallback()

    def create_basic_controls(self):
        # Brightness
        Label(self.basic_tab, text="Brightness (-100 to 100):").pack(anchor=tk.W)
        Scale(
            self.basic_tab,
            from_=-100,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.brightness,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Contrast
        Label(self.basic_tab, text="Contrast (0.5 to 3.0):").pack(anchor=tk.W)
        Scale(
            self.basic_tab,
            from_=0.5,
            to=3.0,
            orient=tk.HORIZONTAL,
            resolution=0.1,
            variable=self.contrast,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Sharpness
        Label(self.basic_tab, text="Sharpness (0.0 to 5.0):").pack(anchor=tk.W)
        Scale(
            self.basic_tab,
            from_=0.0,
            to=5.0,
            orient=tk.HORIZONTAL,
            resolution=0.1,
            variable=self.sharpness,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Threshold
        Label(self.basic_tab, text="Threshold Method:").pack(anchor=tk.W)
        methods_frame = Frame(self.basic_tab, bg="#f0f0f0")
        methods_frame.pack(fill=tk.X)

        threshold_methods = [
            ("None", "none"),
            ("Binary", "binary"),
            ("Adaptive", "adaptive"),
            ("Otsu", "otsu"),
        ]

        for text, method in threshold_methods:
            tk.Radiobutton(
                methods_frame,
                text=text,
                variable=self.threshold_method,
                value=method,
                bg="#f0f0f0",
                command=self.update_preview,
            ).pack(side=tk.LEFT)

        # Threshold value for binary threshold
        Label(self.basic_tab, text="Threshold Value (0-255):").pack(anchor=tk.W)
        Scale(
            self.basic_tab,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self.threshold_value,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Adaptive threshold parameters
        Label(self.basic_tab, text="Adaptive Block Size (3-51, odd only):").pack(
            anchor=tk.W
        )
        Scale(
            self.basic_tab,
            from_=3,
            to=51,
            orient=tk.HORIZONTAL,
            variable=self.adaptive_block_size,
            command=self.update_preview,
        ).pack(fill=tk.X)

        Label(self.basic_tab, text="Adaptive C Value (0-20):").pack(anchor=tk.W)
        Scale(
            self.basic_tab,
            from_=0,
            to=20,
            orient=tk.HORIZONTAL,
            variable=self.adaptive_c,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Invert
        Checkbutton(
            self.basic_tab,
            text="Invert Colors",
            variable=self.invert,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(anchor=tk.W, pady=5)

        # Reset button
        Button(
            self.basic_tab, text="Reset Basic Parameters", command=self.reset_parameters
        ).pack(fill=tk.X, pady=10)

    def create_basic_controls_fallback(self):
        # Fallback method if ttk is not available
        # Brightness
        Label(self.control_frame, text="Brightness (-100 to 100):").pack(anchor=tk.W)
        Scale(
            self.control_frame,
            from_=-100,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.brightness,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Contrast
        Label(self.control_frame, text="Contrast (0.5 to 3.0):").pack(anchor=tk.W)
        Scale(
            self.control_frame,
            from_=0.5,
            to=3.0,
            orient=tk.HORIZONTAL,
            resolution=0.1,
            variable=self.contrast,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Threshold
        Label(self.control_frame, text="Threshold Method:").pack(anchor=tk.W)
        methods_frame = Frame(self.control_frame, bg="#f0f0f0")
        methods_frame.pack(fill=tk.X)

        threshold_methods = [
            ("None", "none"),
            ("Binary", "binary"),
            ("Adaptive", "adaptive"),
            ("Otsu", "otsu"),
        ]

        for text, method in threshold_methods:
            tk.Radiobutton(
                methods_frame,
                text=text,
                variable=self.threshold_method,
                value=method,
                bg="#f0f0f0",
                command=self.update_preview,
            ).pack(side=tk.LEFT)

        # Reset button
        Button(
            self.control_frame, text="Reset Parameters", command=self.reset_parameters
        ).pack(fill=tk.X, pady=10)

    def create_advanced_controls(self):
        # Bilateral Filter section
        filter_frame = Frame(self.advanced_tab, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        filter_frame.pack(fill=tk.X, pady=5)

        Label(
            filter_frame,
            text="Bilateral Filter (preserves edges like commas and dots)",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        ).pack(anchor=tk.W)

        Checkbutton(
            filter_frame,
            text="Use Bilateral Filter",
            variable=self.use_bilateral,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(anchor=tk.W)

        Label(filter_frame, text="Diameter (5-25):").pack(anchor=tk.W)
        Scale(
            filter_frame,
            from_=5,
            to=25,
            orient=tk.HORIZONTAL,
            variable=self.bilateral_d,
            command=self.update_preview,
        ).pack(fill=tk.X)

        Label(filter_frame, text="Sigma Color (5-75):").pack(anchor=tk.W)
        Scale(
            filter_frame,
            from_=5,
            to=75,
            orient=tk.HORIZONTAL,
            variable=self.bilateral_sigma_color,
            command=self.update_preview,
        ).pack(fill=tk.X)

        Label(filter_frame, text="Sigma Space (5-75):").pack(anchor=tk.W)
        Scale(
            filter_frame,
            from_=5,
            to=75,
            orient=tk.HORIZONTAL,
            variable=self.bilateral_sigma_space,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # CLAHE section
        clahe_frame = Frame(self.advanced_tab, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        clahe_frame.pack(fill=tk.X, pady=5)

        Label(
            clahe_frame,
            text="CLAHE (enhances local contrast)",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        ).pack(anchor=tk.W)

        Checkbutton(
            clahe_frame,
            text="Use CLAHE",
            variable=self.use_clahe,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(anchor=tk.W)

        Label(clahe_frame, text="Clip Limit (0.5-5.0):").pack(anchor=tk.W)
        Scale(
            clahe_frame,
            from_=0.5,
            to=5.0,
            orient=tk.HORIZONTAL,
            resolution=0.1,
            variable=self.clahe_clip_limit,
            command=self.update_preview,
        ).pack(fill=tk.X)

        Label(clahe_frame, text="Grid Size (2-16):").pack(anchor=tk.W)
        Scale(
            clahe_frame,
            from_=2,
            to=16,
            orient=tk.HORIZONTAL,
            variable=self.clahe_grid_size,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Glare Reduction section
        glare_frame = Frame(self.advanced_tab, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        glare_frame.pack(fill=tk.X, pady=5)

        Label(
            glare_frame,
            text="Glare Reduction (recovers text in bright areas)",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        ).pack(anchor=tk.W)

        Checkbutton(
            glare_frame,
            text="Use Glare Reduction",
            variable=self.use_glare_reduction,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(anchor=tk.W)

        Label(glare_frame, text="Glare Threshold (150-250):").pack(anchor=tk.W)
        Scale(
            glare_frame,
            from_=150,
            to=250,
            orient=tk.HORIZONTAL,
            variable=self.glare_threshold,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # LAB Color Space section
        lab_frame = Frame(self.advanced_tab, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        lab_frame.pack(fill=tk.X, pady=5)

        Label(
            lab_frame,
            text="LAB Color Processing (handles varying lighting)",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        ).pack(anchor=tk.W)

        Checkbutton(
            lab_frame,
            text="Use LAB Color Space",
            variable=self.use_lab,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(anchor=tk.W)

        Checkbutton(
            lab_frame,
            text="Enhance L Channel",
            variable=self.l_enhance,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(anchor=tk.W)

        # Morphology section
        morph_frame = Frame(self.advanced_tab, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        morph_frame.pack(fill=tk.X, pady=5)

        Label(
            morph_frame,
            text="Morphology (cleans up text)",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        ).pack(anchor=tk.W)

        Label(morph_frame, text="Kernel Size (1-3):").pack(anchor=tk.W)
        Scale(
            morph_frame,
            from_=1,
            to=3,
            orient=tk.HORIZONTAL,
            variable=self.kernel_size,
            command=self.update_preview,
        ).pack(fill=tk.X)

        morph_options = Frame(morph_frame, bg="#f0f0f0")
        morph_options.pack(fill=tk.X)

        Checkbutton(
            morph_options,
            text="Opening",
            variable=self.use_opening,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(side=tk.LEFT)

        Checkbutton(
            morph_options,
            text="Closing",
            variable=self.use_closing,
            bg="#f0f0f0",
            command=self.update_preview,
        ).pack(side=tk.LEFT)

        # Blur
        Label(self.advanced_tab, text="Blur Size (0 for none, 3-15, odd only):").pack(
            anchor=tk.W
        )
        Scale(
            self.advanced_tab,
            from_=0,
            to=15,
            orient=tk.HORIZONTAL,
            variable=self.blur_size,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Morphological operations
        Label(self.advanced_tab, text="Dilate Iterations (0 for none):").pack(
            anchor=tk.W
        )
        Scale(
            self.advanced_tab,
            from_=0,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.dilate_iterations,
            command=self.update_preview,
        ).pack(fill=tk.X)

        Label(self.advanced_tab, text="Erode Iterations (0 for none):").pack(
            anchor=tk.W
        )
        Scale(
            self.advanced_tab,
            from_=0,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.erode_iterations,
            command=self.update_preview,
        ).pack(fill=tk.X)

        # Reset button
        Button(
            self.advanced_tab,
            text="Reset Advanced Parameters",
            command=self.reset_advanced_parameters,
        ).pack(fill=tk.X, pady=10)

    def create_presets(self):
        Label(
            self.presets_tab,
            text="Preset Configurations for Ingredient Labels",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preset for punctuation enhancement
        Button(
            self.presets_tab,
            text="Punctuation Enhancement",
            command=self.preset_punctuation,
        ).pack(fill=tk.X, pady=2)
        Label(
            self.presets_tab,
            text="Optimized for commas, dots and small characters",
            bg="#f0f0f0",
            fg="#555555",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preset for glare handling
        Button(
            self.presets_tab, text="Glare Reduction", command=self.preset_glare
        ).pack(fill=tk.X, pady=2)
        Label(
            self.presets_tab,
            text="Reduces washout in bright areas of packaging",
            bg="#f0f0f0",
            fg="#555555",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preset for multi-technique approach
        Button(
            self.presets_tab,
            text="Multi-technique OCR Optimization",
            command=self.preset_multi_technique,
        ).pack(fill=tk.X, pady=2)
        Label(
            self.presets_tab,
            text="Comprehensive processing pipeline for best results",
            bg="#f0f0f0",
            fg="#555555",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preset for high contrast labels
        Button(
            self.presets_tab,
            text="High Contrast Labels",
            command=self.preset_high_contrast,
        ).pack(fill=tk.X, pady=2)
        Label(
            self.presets_tab,
            text="For clear black text on white background",
            bg="#f0f0f0",
            fg="#555555",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preset for low contrast labels
        Button(
            self.presets_tab,
            text="Low Contrast/Faded Text",
            command=self.preset_low_contrast,
        ).pack(fill=tk.X, pady=2)
        Label(
            self.presets_tab,
            text="For faded or low contrast ingredient lists",
            bg="#f0f0f0",
            fg="#555555",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preset for small text
        Button(
            self.presets_tab,
            text="Small Text Enhancement",
            command=self.preset_small_text,
        ).pack(fill=tk.X, pady=2)
        Label(
            self.presets_tab,
            text="Optimizes detection of tiny text and punctuation",
            bg="#f0f0f0",
            fg="#555555",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preset for inverted text (white on dark)
        Button(
            self.presets_tab,
            text="Inverted Text (White on Dark)",
            command=self.preset_inverted,
        ).pack(fill=tk.X, pady=2)
        Label(
            self.presets_tab,
            text="For white or light text on dark backgrounds",
            bg="#f0f0f0",
            fg="#555555",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Display area
        self.image_label = Label(
            self.display_frame, bg="#d0d0d0", text="No image loaded"
        )
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")]
        )

        if file_path:
            self.file_path = file_path
            self.original_img = cv2.imread(file_path)

            if self.original_img is None:
                # Try with PIL if OpenCV fails
                try:
                    pil_img = Image.open(file_path)
                    self.original_img = np.array(pil_img)
                    if len(self.original_img.shape) == 2:  # Grayscale
                        self.original_img = cv2.cvtColor(
                            self.original_img, cv2.COLOR_GRAY2BGR
                        )
                    else:  # Color
                        self.original_img = cv2.cvtColor(
                            self.original_img, cv2.COLOR_RGB2BGR
                        )
                except Exception as e:
                    print(f"Error loading image: {e}")
                    return

            self.reset_parameters()
            self.update_preview()

    def update_preview(self, *args):
        if self.original_img is None:
            return

        # Make sure adaptive block size is odd
        block_size = self.adaptive_block_size.get()
        if block_size % 2 == 0:
            self.adaptive_block_size.set(block_size + 1)

        # Make sure blur size is odd and at least 3 if not 0
        blur_size = self.blur_size.get()
        if blur_size > 0:
            if blur_size % 2 == 0:
                self.blur_size.set(blur_size + 1)
            if blur_size < 3:
                self.blur_size.set(3)

        # Start with a copy of the original image
        img = self.original_img.copy()

        # Process using LAB color space if selected
        if self.use_lab.get() == 1:
            img = self._process_lab(img)

        # Convert to grayscale if not already
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Apply CLAHE if selected (before other adjustments)
        if self.use_clahe.get() == 1:
            clahe = cv2.createCLAHE(
                clipLimit=self.clahe_clip_limit.get(),
                tileGridSize=(self.clahe_grid_size.get(), self.clahe_grid_size.get()),
            )
            gray = clahe.apply(gray)

        # Apply glare reduction if selected
        if self.use_glare_reduction.get() == 1:
            gray = self._reduce_glare(gray)

        # Apply brightness and contrast adjustments
        brightness = self.brightness.get()
        contrast = self.contrast.get()

        if brightness != 0 or contrast != 1.0:
            gray = cv2.convertScaleAbs(gray, alpha=contrast, beta=brightness)

        # Apply bilateral filter if selected
        if self.use_bilateral.get() == 1:
            gray = cv2.bilateralFilter(
                gray,
                self.bilateral_d.get(),
                self.bilateral_sigma_color.get(),
                self.bilateral_sigma_space.get(),
            )

        # Apply sharpening if specified
        sharpness = self.sharpness.get()
        if sharpness > 0:
            kernel = np.array([[-1, -1, -1], [-1, 9 + sharpness, -1], [-1, -1, -1]]) / (
                sharpness + 5
            )
            gray = cv2.filter2D(gray, -1, kernel)

        # Apply blur if specified
        blur_size = self.blur_size.get()
        if blur_size > 0:
            gray = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)

        # Apply thresholding based on selected method
        threshold_method = self.threshold_method.get()

        if threshold_method == "binary":
            _, gray = cv2.threshold(
                gray, self.threshold_value.get(), 255, cv2.THRESH_BINARY
            )
        elif threshold_method == "adaptive":
            gray = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.adaptive_block_size.get(),
                self.adaptive_c.get(),
            )
        elif threshold_method == "otsu":
            _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Apply morphological operations
        kernel_size = self.kernel_size.get()
        kernel = np.ones((kernel_size, kernel_size), np.uint8)

        # Opening (erode then dilate) to remove small noise
        if self.use_opening.get() == 1:
            gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=1)

        # Closing (dilate then erode) to close small gaps
        if self.use_closing.get() == 1:
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Traditional morphological operations
        if self.dilate_iterations.get() > 0:
            gray = cv2.dilate(gray, kernel, iterations=self.dilate_iterations.get())

        if self.erode_iterations.get() > 0:
            gray = cv2.erode(gray, kernel, iterations=self.erode_iterations.get())

        # Invert if needed
        if self.invert.get() == 1:
            gray = cv2.bitwise_not(gray)

        # Store the processed image
        self.processed_img = gray

        # Display the image
        self.display_image(gray)

    def _process_lab(self, image):
        """Process image in LAB color space to enhance contrast"""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Split the LAB channels
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel if L enhancement is selected
        if self.l_enhance.get() == 1:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

        # Merge the channels back
        lab = cv2.merge((l, a, b))

        # Convert back to BGR
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _reduce_glare(self, gray_image):
        """Reduce glare in grayscale image"""
        # Create a mask to identify glare areas
        _, mask = cv2.threshold(
            gray_image, self.glare_threshold.get(), 255, cv2.THRESH_BINARY_INV
        )

        # Apply the mask
        result = cv2.bitwise_and(gray_image, gray_image, mask=mask)

        # Normalize to use full dynamic range
        result = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX)

        return result

    def display_image(self, img):
        h, w = img.shape[:2]

        # Calculate dimensions to fit display area
        display_w = self.display_frame.winfo_width() - 20
        display_h = self.display_frame.winfo_height() - 20

        if display_w <= 1 or display_h <= 1:  # Not yet properly sized
            display_w, display_h = 800, 600

        # Calculate aspect ratio preserved dimensions
        ratio = min(display_w / w, display_h / h)
        new_w, new_h = int(w * ratio), int(h * ratio)

        # Resize for display (not affecting the processed image)
        display_img = cv2.resize(img, (new_w, new_h))

        # Convert to PIL format for Tkinter
        if len(display_img.shape) == 2:  # Grayscale
            pil_img = Image.fromarray(display_img)
        else:  # Color
            display_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(display_img)

        # Convert to Tkinter format
        tk_img = ImageTk.PhotoImage(pil_img)

        # Update displayed image
        self.image_label.config(image=tk_img, text="")
        self.image_label.image = tk_img  # Keep a reference
        self.displayed_img = tk_img

    def save_image(self):
        if self.processed_img is None:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            cv2.imwrite(file_path, self.processed_img)

    def save_variants(self):
        """Generate and save multiple variants of the processed image optimized for OCR of ingredient lists"""
        if self.original_img is None:
            return

        # Ask for directory to save variants
        save_dir = filedialog.askdirectory()
        if not save_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(self.file_path) if self.file_path else "image"
        base_name = os.path.splitext(base_name)[0]

        # Store all current parameters
        self.store_current_params()

        # Create OCR-optimized variations
        variants = []

        # Apply each preset and save the result
        # Variant 1: Punctuation Enhancement
        self.preset_punctuation()
        variants.append(("punctuation_enhancement", self.processed_img.copy()))

        # Variant 2: Small Text Enhancement
        self.preset_small_text()
        variants.append(("small_text", self.processed_img.copy()))

        # Variant 3: Glare Reduction
        self.preset_glare()
        variants.append(("glare_reduction", self.processed_img.copy()))

        # Variant 4: Multi-technique Approach
        self.preset_multi_technique()
        variants.append(("multi_technique", self.processed_img.copy()))

        # Variant 5: High Contrast
        self.preset_high_contrast()
        variants.append(("high_contrast", self.processed_img.copy()))

        # Variant 6: Low Contrast/Faded Text
        self.preset_low_contrast()
        variants.append(("low_contrast", self.processed_img.copy()))

        # Variant 7: Inverted Text
        self.preset_inverted()
        variants.append(("inverted", self.processed_img.copy()))

        # Variant 8: Traditional approach with bilateral filter
        self.reset_parameters()
        self.contrast.set(1.5)
        self.brightness.set(0)
        self.use_bilateral.set(1)
        self.bilateral_d.set(9)
        self.bilateral_sigma_color.set(15)
        self.bilateral_sigma_space.set(15)
        self.threshold_method.set("adaptive")
        self.adaptive_block_size.set(11)
        self.adaptive_c.set(2)
        self.update_preview()
        variants.append(("bilateral_filter", self.processed_img.copy()))

        # Save all variants
        for name, img in variants:
            save_path = os.path.join(save_dir, f"{base_name}_{name}_{timestamp}.png")
            cv2.imwrite(save_path, img)

        # Restore original parameters
        self.restore_saved_params()

        # Show confirmation message
        messagebox.showinfo(
            "Variants Saved",
            f"Saved {len(variants)} image variants optimized for OCR to {save_dir}",
        )

    def store_current_params(self):
        """Store all current parameters for later restoration"""
        self.saved_params = {
            # Basic parameters
            "brightness": self.brightness.get(),
            "contrast": self.contrast.get(),
            "sharpness": self.sharpness.get(),
            "threshold_method": self.threshold_method.get(),
            "threshold_value": self.threshold_value.get(),
            "adaptive_block_size": self.adaptive_block_size.get(),
            "adaptive_c": self.adaptive_c.get(),
            "blur_size": self.blur_size.get(),
            "dilate_iterations": self.dilate_iterations.get(),
            "erode_iterations": self.erode_iterations.get(),
            "invert": self.invert.get(),
            # Advanced parameters
            "bilateral_d": self.bilateral_d.get(),
            "bilateral_sigma_color": self.bilateral_sigma_color.get(),
            "bilateral_sigma_space": self.bilateral_sigma_space.get(),
            "use_bilateral": self.use_bilateral.get(),
            "use_clahe": self.use_clahe.get(),
            "clahe_clip_limit": self.clahe_clip_limit.get(),
            "clahe_grid_size": self.clahe_grid_size.get(),
            "use_glare_reduction": self.use_glare_reduction.get(),
            "glare_threshold": self.glare_threshold.get(),
            "kernel_size": self.kernel_size.get(),
            "use_opening": self.use_opening.get(),
            "use_closing": self.use_closing.get(),
            "use_lab": self.use_lab.get(),
            "l_enhance": self.l_enhance.get(),
        }

    def restore_saved_params(self):
        """Restore parameters from saved state"""
        if not hasattr(self, "saved_params"):
            return

        # Restore all parameters
        for param, value in self.saved_params.items():
            if hasattr(self, param):
                var = getattr(self, param)
                if hasattr(var, "set"):
                    var.set(value)

        self.update_preview()

    def reset_parameters(self):
        """Reset all basic parameters to default values"""
        self.brightness.set(0)
        self.contrast.set(1.0)
        self.sharpness.set(0.0)
        self.threshold_method.set("adaptive")
        self.threshold_value.set(127)
        self.adaptive_block_size.set(11)
        self.adaptive_c.set(2)
        self.blur_size.set(0)
        self.dilate_iterations.set(0)
        self.erode_iterations.set(0)
        self.invert.set(0)
        self.reset_advanced_parameters()
        self.update_preview()

    def reset_advanced_parameters(self):
        """Reset advanced parameters to default values"""
        self.bilateral_d.set(9)
        self.bilateral_sigma_color.set(15)
        self.bilateral_sigma_space.set(15)
        self.use_bilateral.set(0)

        self.use_clahe.set(0)
        self.clahe_clip_limit.set(2.0)
        self.clahe_grid_size.set(8)

        self.use_glare_reduction.set(0)
        self.glare_threshold.set(200)

        self.kernel_size.set(2)
        self.use_opening.set(0)
        self.use_closing.set(0)

        self.use_lab.set(0)
        self.l_enhance.set(0)
        self.update_preview()

    def preset_punctuation(self):
        """Apply preset for punctuation enhancement"""
        # Reset first to clear any existing settings
        self.reset_parameters()

        # Basic settings
        self.brightness.set(0)
        self.contrast.set(1.3)
        self.sharpness.set(1.0)
        self.threshold_method.set("adaptive")
        self.adaptive_block_size.set(9)  # Smaller block size for finer details
        self.adaptive_c.set(2)

        # Advanced settings
        self.use_bilateral.set(1)
        self.bilateral_d.set(9)
        self.bilateral_sigma_color.set(15)
        self.bilateral_sigma_space.set(15)

        self.kernel_size.set(2)  # Smaller kernel for preserving small details
        self.use_closing.set(1)  # Closing helps connect broken parts of text

        self.update_preview()
        messagebox.showinfo(
            "Preset Applied",
            "Punctuation Enhancement preset applied. This preset is optimized for detecting commas, periods, and other small characters.",
        )

    def preset_glare(self):
        """Apply preset for glare reduction"""
        # Reset first to clear any existing settings
        self.reset_parameters()

        # Basic settings
        self.brightness.set(-5)  # Slightly darken
        self.contrast.set(1.2)

        # Advanced settings
        self.use_lab.set(1)
        self.l_enhance.set(1)
        self.use_glare_reduction.set(1)
        self.glare_threshold.set(220)

        self.use_clahe.set(1)
        self.clahe_clip_limit.set(3.0)
        self.clahe_grid_size.set(8)

        self.threshold_method.set("adaptive")
        self.adaptive_block_size.set(15)
        self.adaptive_c.set(5)

        self.update_preview()
        messagebox.showinfo(
            "Preset Applied",
            "Glare Reduction preset applied. This preset is designed to recover text in washed-out or bright areas of packaging.",
        )

    def preset_multi_technique(self):
        """Apply preset for multi-technique approach"""
        # Reset first to clear any existing settings
        self.reset_parameters()

        # This preset uses a combination of techniques
        self.contrast.set(1.5)

        self.use_clahe.set(1)
        self.clahe_clip_limit.set(2.5)

        self.use_bilateral.set(1)
        self.bilateral_d.set(9)
        self.bilateral_sigma_color.set(20)
        self.bilateral_sigma_space.set(20)

        self.threshold_method.set("adaptive")
        self.adaptive_block_size.set(11)
        self.adaptive_c.set(2)

        self.kernel_size.set(2)
        self.use_closing.set(1)

        self.blur_size.set(3)  # Light blur at the end

        self.update_preview()
        messagebox.showinfo(
            "Preset Applied",
            "Multi-technique OCR Optimization preset applied. This comprehensive approach handles various image quality issues while preserving small details.",
        )

    def preset_high_contrast(self):
        """Apply preset for high contrast labels"""
        # Reset first to clear any existing settings
        self.reset_parameters()

        # Simple but effective settings for clear text
        self.brightness.set(10)
        self.contrast.set(2.0)

        self.threshold_method.set("binary")
        self.threshold_value.set(160)

        self.dilate_iterations.set(1)

        self.update_preview()
        messagebox.showinfo(
            "Preset Applied",
            "High Contrast Labels preset applied. This preset works well for clear black text on white backgrounds.",
        )

    def preset_low_contrast(self):
        """Apply preset for low contrast or faded text"""
        # Reset first to clear any existing settings
        self.reset_parameters()

        # Enhance contrast significantly
        self.brightness.set(0)
        self.contrast.set(2.0)

        self.use_clahe.set(1)
        self.clahe_clip_limit.set(4.0)
        self.clahe_grid_size.set(8)

        self.threshold_method.set("adaptive")
        self.adaptive_block_size.set(15)
        self.adaptive_c.set(5)

        self.update_preview()
        messagebox.showinfo(
            "Preset Applied",
            "Low Contrast/Faded Text preset applied. This preset enhances visibility of faded or low contrast ingredient lists.",
        )

    def preset_small_text(self):
        """Apply preset for small text enhancement"""
        # Reset first to clear any existing settings
        self.reset_parameters()

        # Settings for tiny text
        self.brightness.set(0)
        self.contrast.set(1.5)
        self.sharpness.set(2.0)  # Increase sharpness significantly

        self.use_bilateral.set(1)
        self.bilateral_d.set(7)  # Smaller value for finer details
        self.bilateral_sigma_color.set(10)
        self.bilateral_sigma_space.set(10)

        self.threshold_method.set("adaptive")
        self.adaptive_block_size.set(7)  # Smaller block size for tiny text
        self.adaptive_c.set(2)

        # No morphological operations to avoid destroying small details

        self.update_preview()
        messagebox.showinfo(
            "Preset Applied",
            "Small Text Enhancement preset applied. This preset is optimized for tiny text and punctuation marks.",
        )

    def preset_inverted(self):
        """Apply preset for inverted text (white on dark)"""
        # Reset first to clear any existing settings
        self.reset_parameters()

        # Settings for inverted text
        self.brightness.set(10)
        self.contrast.set(1.5)

        self.threshold_method.set("adaptive")
        self.adaptive_block_size.set(15)
        self.adaptive_c.set(10)

        self.invert.set(1)  # Invert the colors

        self.dilate_iterations.set(1)  # Slightly thicken text after inversion

        self.update_preview()
        messagebox.showinfo(
            "Preset Applied",
            "Inverted Text preset applied. This preset works well for white or light text on dark backgrounds.",
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorGUI(root)
    root.mainloop()
