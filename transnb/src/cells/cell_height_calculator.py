from PyQt5.QtWidgets import QWidget
from typing import Tuple, Optional
from utils.size_calculator import SizeCalculator
from cells.cell_config import CellConfig


class CellHeightCalculator:
    """单元格高度计算器类，负责处理所有与单元格高度相关的计算逻辑"""

    @classmethod
    def calculate_viewport_width(cls, editor_widget, content_area: QWidget, cell_widget: QWidget) -> int:
        """
        计算用于文档折行的视口宽度，优先使用编辑器视口宽度，避免低估行数导致内容被裁切
        
        Args:
            editor_widget: 编辑器组件（MarkdownEditor实例）
            content_area: 单元格内容区域
            cell_widget: 单元格自身
            
        Returns:
            可用的视口宽度（像素）
        """
        # 优先尝试从编辑器的阅读模式和编辑模式中获取有效视口宽度
        for text_edit in (editor_widget.reading, editor_widget.editor):
            viewport_width = text_edit.viewport().width()
            if viewport_width > 50:
                return viewport_width
        
        # 其次尝试使用内容区域宽度
        content_area_width = content_area.width()
        if content_area_width > 50:
            return max(50, content_area_width - 16)
        
        # 最后使用单元格自身宽度
        cell_width = cell_widget.width()
        if cell_width > 80:
            return max(50, cell_width - 50)
        
        # 返回默认宽度
        return 400

    @classmethod
    def calculate_document_height(cls, editor_widget, viewport_width: int) -> int:
        """
        计算编辑器文档的高度，取阅读模式和编辑模式的较大值，确保切换模式后高度足够
        
        Args:
            editor_widget: 编辑器组件（MarkdownEditor实例）
            viewport_width: 视口宽度
            
        Returns:
            文档高度（像素）
        """
        reading_height = SizeCalculator.calculate_precise_height(
            editor_widget.reading, viewport_width
        )
        editing_height = SizeCalculator.calculate_precise_height(
            editor_widget.editor, viewport_width
        )
        return max(reading_height, editing_height)

    @classmethod
    def calculate_section_height(
        cls,
        is_collapsed: bool,
        document_height: int
    ) -> int:
        """
        计算单个区段（原文或翻译）的高度，考虑折叠状态
        
        Args:
            is_collapsed: 该区段是否折叠
            document_height: 文档高度（展开时使用）
            
        Returns:
            区段高度（像素）
        """
        if is_collapsed:
            # 折叠时：标签高度 + 省略号标签高度
            return CellConfig.LABEL_HEIGHT + CellConfig.COLLAPSED_SECTION_EXTRA
        else:
            # 展开时：标签高度 + 编辑器边距 + 文档高度 + 区段额外高度
            return (
                CellConfig.LABEL_HEIGHT 
                + CellConfig.EDITOR_CHROME 
                + document_height 
                + CellConfig.SECTION_EXTRA
            )

    @classmethod
    def calculate_total_height(
        cls,
        is_cell_collapsed: bool,
        is_input_collapsed: bool,
        is_output_collapsed: bool,
        input_doc_height: int,
        output_doc_height: int,
        content_margin_v: int,
        min_height: int = CellConfig.MIN_HEIGHT,
        max_height: int = CellConfig.MAX_HEIGHT
    ) -> int:
        """
        计算单元格的总高度
        
        Args:
            is_cell_collapsed: 整个单元格是否折叠
            is_input_collapsed: 原文区段是否折叠
            is_output_collapsed: 翻译区段是否折叠
            input_doc_height: 原文文档高度
            output_doc_height: 翻译文档高度
            content_margin_v: 内容区域垂直边距总和
            min_height: 单元格最小高度
            max_height: 单元格最大高度
            
        Returns:
            单元格总高度（像素）
        """
        if is_cell_collapsed:
            # 整个单元格折叠时，直接返回折叠高度
            return CellConfig.COLLAPSED_CELL_HEIGHT
        
        # 计算各区段高度
        input_section_h = cls.calculate_section_height(is_input_collapsed, input_doc_height)
        output_section_h = cls.calculate_section_height(is_output_collapsed, output_doc_height)
        
        # 总高度 = 原文区段高度 + 翻译区段高度 + 分割条高度 + 内容区域垂直边距
        total_height = int(
            input_section_h 
            + output_section_h 
            + CellConfig.SPLITTER_HANDLE 
            + content_margin_v
        )
        
        # 应用最小和最大高度限制
        return max(min_height, min(total_height, max_height))

    @classmethod
    def get_splitter_sizes(
        cls,
        is_cell_collapsed: bool,
        is_input_collapsed: bool,
        is_output_collapsed: bool,
        input_doc_height: int,
        output_doc_height: int
    ) -> Tuple[int, int]:
        """
        获取分割条的尺寸配置
        
        Args:
            is_cell_collapsed: 整个单元格是否折叠
            is_input_collapsed: 原文区段是否折叠
            is_output_collapsed: 翻译区段是否折叠
            input_doc_height: 原文文档高度
            output_doc_height: 翻译文档高度
            
        Returns:
            (原文区段高度, 翻译区段高度) 元组
        """
        if is_cell_collapsed:
            # 单元格折叠时返回默认尺寸
            return (42, 42)
        
        input_section_h = cls.calculate_section_height(is_input_collapsed, input_doc_height)
        output_section_h = cls.calculate_section_height(is_output_collapsed, output_doc_height)
        
        # 确保最小高度至少为 42 像素
        return (max(42, input_section_h), max(42, output_section_h))

    @classmethod
    def calculate_height_for_cell(
        cls,
        cell_widget: QWidget,
        content_area: QWidget,
        content_layout,
        input_editor,
        output_editor,
        is_cell_collapsed: bool,
        is_input_collapsed: bool,
        is_output_collapsed: bool,
        min_height: int = CellConfig.MIN_HEIGHT,
        max_height: int = CellConfig.MAX_HEIGHT
    ) -> Tuple[int, int, int, Tuple[int, int]]:
        """
        为单元格计算完整的高度信息，包含文档高度和分割条尺寸
        
        Args:
            cell_widget: 单元格组件
            content_area: 内容区域组件
            content_layout: 内容布局（用于获取边距）
            input_editor: 原文编辑器
            output_editor: 翻译编辑器
            is_cell_collapsed: 单元格是否折叠
            is_input_collapsed: 原文是否折叠
            is_output_collapsed: 翻译是否折叠
            min_height: 最小高度
            max_height: 最大高度
            
        Returns:
            (总高度, 原文文档高度, 翻译文档高度, 分割条尺寸) 元组
        """
        # 计算视口宽度
        input_vw = cls.calculate_viewport_width(input_editor, content_area, cell_widget)
        output_vw = cls.calculate_viewport_width(output_editor, content_area, cell_widget)
        
        # 计算文档高度
        input_doc_h = cls.calculate_document_height(input_editor, input_vw)
        output_doc_h = cls.calculate_document_height(output_editor, output_vw)
        
        # 计算内容区域垂直边距
        margins = content_layout.contentsMargins()
        content_margin_v = margins.top() + margins.bottom()
        
        # 计算总高度
        total_height = cls.calculate_total_height(
            is_cell_collapsed=is_cell_collapsed,
            is_input_collapsed=is_input_collapsed,
            is_output_collapsed=is_output_collapsed,
            input_doc_height=input_doc_h,
            output_doc_height=output_doc_h,
            content_margin_v=content_margin_v,
            min_height=min_height,
            max_height=max_height
        )
        
        # 计算分割条尺寸
        splitter_sizes = cls.get_splitter_sizes(
            is_cell_collapsed=is_cell_collapsed,
            is_input_collapsed=is_input_collapsed,
            is_output_collapsed=is_output_collapsed,
            input_doc_height=input_doc_h,
            output_doc_height=output_doc_h
        )
        
        return (total_height, input_doc_h, output_doc_h, splitter_sizes)
