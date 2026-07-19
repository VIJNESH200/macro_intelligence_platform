"""
App — Main GUI orchestrator for the Macro Intelligence Platform.
=================================================================
Replaces the monolithic main() function from business_cycle_tracer.py.
Ties together layout, sidebars, widgets, animation, and export.
"""
import os
import math
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.widgets import Slider, Button, CheckButtons, RadioButtons
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection

from .layout import create_figure, create_main_axes, create_background_axes, draw_group_container
from .sidebars import create_sparkline_axes, create_left_sidebar, create_right_sidebar, create_market_panel


class App:
    """Main application class — creates the GUI and runs the event loop."""

    def __init__(self, df: pd.DataFrame, spline_data: pd.DataFrame,
                 config: dict, market_series: dict, data_metadata: dict = None):
        self.df = df
        self.spline_data = spline_data
        self.config = config
        self.market_series = market_series
        self.data_metadata = data_metadata or {}
        self.max_frames = len(df) - 1
        self.state = {'current_frame': 0, 'is_playing': False}
        self.export_menu = {}

        self._build_ui()
        self._wire_callbacks()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        df, config = self.df, self.config

        # Figure + main axes
        self.fig = create_figure(config)
        self.ax = create_main_axes(self.fig, df, config)

        # Sparkline
        self.ax_spark, self.spark_pt = create_sparkline_axes(self.fig, df)

        # Left sidebar
        left = create_left_sidebar(self.fig)

        # Right sidebar
        right = create_right_sidebar(self.fig)

        # Market panel
        (self.ax_market, market_texts, market_sep, market_header,
         ax_market_mode, btn_market_mode,
         ax_market_cfg, btn_market_cfg) = create_market_panel(self.fig, self.market_series)

        # Slider
        ax_slider = self.fig.add_axes([0.16, 0.10, 0.68, 0.02])
        self.slider = Slider(ax_slider, '', 0, self.max_frames,
                             valinit=0, valstep=1, color='#1f497d', initcolor='none')
        self.slider.valtext.set_visible(False)

        # Background for control groups
        ax_bg = create_background_axes(self.fig)
        control_bg_elements = []

        pad = 0.005
        grp_y, grp_h = 0.020, 0.070

        # Group 1: Playback
        control_bg_elements += draw_group_container(self.fig, ax_bg, 0.16, grp_y, 0.16, grp_h, "Playback")
        ax_play = self.fig.add_axes([0.165, 0.028, 0.045, 0.035])
        self.btn_play = self._style_button(ax_play, 'Play')
        ax_pause = self.fig.add_axes([0.215, 0.028, 0.045, 0.035])
        self.btn_pause = self._style_button(ax_pause, 'Pause')
        ax_reset = self.fig.add_axes([0.265, 0.028, 0.045, 0.035])
        self.btn_reset = self._style_button(ax_reset, 'Reset')

        # Group 2: Animation
        control_bg_elements += draw_group_container(self.fig, ax_bg, 0.37, grp_y, 0.11, grp_h, "Animation")
        ax_1x = self.fig.add_axes([0.376, 0.028, 0.028, 0.035])
        self.btn_1x = self._style_button(ax_1x, '1x')
        self.btn_1x.label.set_color('#1f497d')
        ax_2x = self.fig.add_axes([0.410, 0.028, 0.028, 0.035])
        self.btn_2x = self._style_button(ax_2x, '2x')
        ax_3x = self.fig.add_axes([0.444, 0.028, 0.028, 0.035])
        self.btn_3x = self._style_button(ax_3x, '3x')

        # Group 3: Display
        control_bg_elements += draw_group_container(self.fig, ax_bg, 0.49, grp_y, 0.22, grp_h, "Display")
        ax_chk_tails = self.fig.add_axes([0.495, 0.045, 0.10, 0.035])
        self.chk_tails = self._style_check(ax_chk_tails, ('Show Tails',), (True,))
        ax_chk_labels = self.fig.add_axes([0.605, 0.045, 0.10, 0.035])
        self.chk_labels = self._style_check(ax_chk_labels, ('Show Labels',), (True,))
        ax_chk_forecast = self.fig.add_axes([0.495, 0.020, 0.10, 0.035])
        self.chk_forecast = self._style_check(ax_chk_forecast, ('Show Forecast',), (True,))
        ax_chk_market = self.fig.add_axes([0.605, 0.020, 0.10, 0.035])
        self.chk_market = self._style_check(ax_chk_market, ('Market Context',), (True,))

        # Group 4: Tools
        control_bg_elements += draw_group_container(self.fig, ax_bg, 0.72, grp_y, 0.12, grp_h, "Tools")
        ax_export = self.fig.add_axes([0.73, 0.028, 0.045, 0.035])
        self.btn_export = self._style_button(ax_export, 'Export')
        ax_help = self.fig.add_axes([0.785, 0.028, 0.045, 0.035])
        self.btn_help = self._style_button(ax_help, 'Help')

        # Open Folder button (hidden)
        ax_open = self.fig.add_axes([0.74, 0.002, 0.08, 0.016])
        self.btn_open = Button(ax_open, 'Open Folder', color='#e9ecef', hovercolor='#dee2e6')
        self.btn_open.label.set_fontsize(8)
        self.btn_open.label.set_color('#1f497d')
        self.btn_open.label.set_fontweight('bold')
        ax_open.set_visible(False)

        # Status bar
        last_update = df.index[-1].strftime('%b %Y')
        default_status = (
            f"Source: {config['source']} | Indicator: {config['name']} | "
            f"Frequency: {config['frequency']} | Window: {config['window']} Months | "
            f"Last Updated: {last_update} | Macro Intelligence Platform v{config['version']}"
        )
        self.fig.add_artist(plt.Line2D([0.01, 0.99], [0.02, 0.02],
                                       color='lightgray', linewidth=1,
                                       transform=self.fig.transFigure))
        status_label = self.fig.text(0.5, 0.01,
                                     "Tip: Click Help (?) to view keyboard shortcuts.",
                                     ha='center', va='center', fontsize=9,
                                     color='#1f497d', fontweight='bold')

        # Chart elements
        current_pt = self.ax.scatter([], [], color='#1f497d', s=90, zorder=6,
                                     edgecolor='white', linewidth=1.5)
        current_label = self.ax.text(0, 0, '', color='black', fontsize=11,
                                     fontweight='bold', ha='left', va='bottom', zorder=7)
        tail_dots = self.ax.scatter([], [], color='dimgray', s=25, zorder=4)
        lc = LineCollection([], linewidth=2.5, zorder=3)
        self.ax.add_collection(lc)
        
        # Forecast chart elements
        self.forecast_line, = self.ax.plot([], [], linestyle='--', color='#dc3545', linewidth=2.5, zorder=5)
        self.forecast_poly = None

        # Collect text lists for export visibility toggling
        left_texts = [left['left_header1'], left['info_date'], left['info_val'],
                      left['info_quad'], left['left_header2'], left['stat_entered'],
                      left['stat_duration'], left['stat_prev']]
        right_texts = [right['right_header1'], right['interp_phase'], right['interp_trend'],
                       right['interp_signal'], right['interp_mom'], right['interp_overall'],
                       right['right_header2'], right['read_health'], right['read_mom'],
                       right['read_dist'], right['read_dir'], right['right_header3']]
                       
        try:
            from ..config import MACRO_SERIES
        except ImportError:
            from config import MACRO_SERIES
        for name in MACRO_SERIES.keys():
            if name in ['Yield 10Y', 'Yield Short']: continue
            right_texts.extend([right[f'driver_{name}_line1'], right[f'driver_{name}_val'], right[f'driver_{name}_line2'], right[f'driver_{name}_pct']])
        right_texts.extend([right['right_header4'], right['fc_base'], right['fc_bull'], right['fc_bear']])

        # Assemble plot_elements dict (same structure as original)
        self.plot_elements = {
            'ax': self.ax, 'current_pt': current_pt, 'current_label': current_label,
            'tail_dots': tail_dots, 'lc': lc,
            'info_date': left['info_date'], 'info_val': left['info_val'],
            'info_quad': left['info_quad'],
            'stat_entered': left['stat_entered'], 'stat_duration': left['stat_duration'],
            'stat_prev': left['stat_prev'],
            'spark_pt': self.spark_pt, 'ax_spark': self.ax_spark,
            'interp_phase': right['interp_phase'], 'interp_trend': right['interp_trend'],
            'interp_signal': right['interp_signal'], 'interp_mom': right['interp_mom'],
            'interp_overall': right['interp_overall'],
            'read_health': right['read_health'], 'read_mom': right['read_mom'],
            'read_dist': right['read_dist'], 'read_dir': right['read_dir'],
            'fc_base': right['fc_base'], 'fc_bull': right['fc_bull'], 'fc_bear': right['fc_bear'],
            'status_label': status_label, 'default_status': default_status,
            'ax_open': ax_open,
            'ax_market': self.ax_market, 'ax_market_cfg': ax_market_cfg,
            'ax_market_mode': ax_market_mode,
            'market_header': market_header, 'market_texts': market_texts,
            'market_sep': market_sep,
            'left_texts': left_texts, 'right_texts': right_texts,
            'left_sep': left['left_sep'], 'right_sep': right['right_sep'],
            'orig_left_x': [t.get_position()[0] for t in left_texts],
            'orig_right_x': [t.get_position()[0] for t in right_texts],
            'orig_spark_pos': self.ax_spark.get_position(),
            'control_axes': [ax_slider, ax_play, ax_pause, ax_reset,
                             ax_1x, ax_2x, ax_3x,
                             ax_chk_tails, ax_chk_labels, ax_chk_market, ax_chk_forecast,
                             ax_export, ax_help, ax_open,
                             ax_market_cfg, ax_market_mode],
            'control_bg_elements': control_bg_elements
        }
        
        for name in MACRO_SERIES.keys():
            if name in ['Yield 10Y', 'Yield Short']: continue
            self.plot_elements[f'driver_{name}_line1'] = right[f'driver_{name}_line1']
            self.plot_elements[f'driver_{name}_val'] = right[f'driver_{name}_val']
            self.plot_elements[f'driver_{name}_line2'] = right[f'driver_{name}_line2']
            self.plot_elements[f'driver_{name}_pct'] = right[f'driver_{name}_pct']

        # Widgets dict for draw_frame compatibility
        self.widgets = {
            'slider': self.slider,
            'btn_play': self.btn_play, 'btn_pause': self.btn_pause,
            'btn_reset': self.btn_reset,
            'btn_1x': self.btn_1x, 'btn_2x': self.btn_2x, 'btn_3x': self.btn_3x,
            'chk_tails': self.chk_tails, 'chk_labels': self.chk_labels,
            'chk_market': self.chk_market, 'chk_forecast': self.chk_forecast,
            'btn_export': self.btn_export, 'btn_help': self.btn_help,
            'btn_open': self.btn_open,
            'btn_market_cfg': btn_market_cfg, 'btn_market_mode': btn_market_mode
        }

        # Market state
        self.plot_elements['market_state'] = {
            'horizon': 1,
            'selected': list(self.market_series.keys())[:5],
            'scroll_y': 0.0,
            'menu_fig': None,
            'mode_fig': None
        }

        self._update_market_layout()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _style_button(ax_btn, label: str) -> Button:
        btn = Button(ax_btn, label, color='#ffffff', hovercolor='#f8f9fa')
        btn.label.set_fontsize(10)
        btn.label.set_fontweight('bold')
        btn.label.set_color('#495057')
        for spine in ax_btn.spines.values():
            spine.set_color('#ced4da')
        return btn

    @staticmethod
    def _style_check(ax_chk, labels, actives) -> CheckButtons:
        ax_chk.set_facecolor('none')
        for spine in ax_chk.spines.values():
            spine.set_visible(False)
        chk = CheckButtons(ax_chk, labels, actives)
        for label in chk.labels:
            label.set_color('#495057')
            label.set_fontsize(9)
        return chk

    def _update_market_layout(self):
        m_state = self.plot_elements['market_state']
        y_pos = 0.95
        for name in self.market_series.keys():
            texts = self.plot_elements['market_texts'][name]
            if name in m_state['selected'] and self.chk_market.get_status()[0]:
                texts['name'].set_y(y_pos)
                texts['val'].set_y(y_pos)
                texts['chg'].set_y(y_pos)
                texts['name'].set_visible(True)
                texts['val'].set_visible(True)
                texts['chg'].set_visible(True)
                y_pos -= 0.16
            else:
                texts['name'].set_visible(False)
                texts['val'].set_visible(False)
                texts['chg'].set_visible(False)

    # ------------------------------------------------------------------
    # Frame Rendering (exact port of draw_frame)
    # ------------------------------------------------------------------
    def draw_frame(self, frame: int):
        idx = int(frame)
        if idx >= len(self.df):
            idx = len(self.df) - 1

        df = self.df
        config = self.config
        pe = self.plot_elements

        show_tails = self.chk_tails.get_status()[0]
        show_labels = self.chk_labels.get_status()[0]
        tail_length = config['tail_length']

        start_idx = max(0, idx - tail_length + 1)
        df_slice = df.iloc[start_idx: idx + 1]
        if df_slice.empty:
            return

        curr_row = df_slice.iloc[-1]
        curr_x, curr_y = curr_row['X'], curr_row['Y']
        date_str = curr_row.name.strftime('%b %Y')

        pe['current_pt'].set_offsets(np.c_[curr_x, curr_y])

        if show_labels:
            pe['current_label'].set_text(f"  {date_str}")
            pe['current_label'].set_position((curr_x, curr_y))
        else:
            pe['current_label'].set_text('')

        pe['info_date'].set_text(f"Date:\n{date_str}")
        pe['info_val'].set_text(f"Value:\n{curr_row['CLI_Raw']:.2f}")

        quad_color = {"Expansion": "darkgreen", "Slowdown": "darkgoldenrod",
                      "Contraction": "darkred", "Recovery": "darkblue"}[curr_row['Quadrant']]
        pe['info_quad'].set_text(f"Quadrant:\n{curr_row['Quadrant']}")
        pe['info_quad'].set_color(quad_color)

        # Cycle Statistics
        curr_quad = curr_row['Quadrant']
        entry_idx = idx
        prev_quad = "--"
        while entry_idx > 0 and df.iloc[entry_idx - 1]['Quadrant'] == curr_quad:
            entry_idx -= 1
        if entry_idx > 0:
            prev_quad = df.iloc[entry_idx - 1]['Quadrant']

        entered_date = df.iloc[entry_idx].name
        duration_months = idx - entry_idx + 1

        pe['stat_entered'].set_text(f"Entered:\n{entered_date.strftime('%b %Y')}")
        pe['stat_duration'].set_text(f"Duration:\n{duration_months} month{'s' if duration_months > 1 else ''}")
        pe['stat_prev'].set_text(f"Previous Phase:\n{prev_quad}")

        import matplotlib.dates as mdates
        pe['spark_pt'].set_offsets(np.c_[mdates.date2num(curr_row.name), curr_row['CLI_Raw']])

        # Right Sidebar
        c = config['center']
        pe['interp_phase'].set_text(f"Current Phase:\n{curr_quad}")

        trend_str = "Strengthening" if curr_y >= c else "Weakening"
        pe['interp_trend'].set_text(f"Trend:\n{trend_str}")

        signal_str = "Above long-term trend" if curr_x >= c else "Below long-term trend"
        pe['interp_signal'].set_text(f"Signal:\n{signal_str}")

        overall_map = {
            "Expansion": "Bullish macro environment",
            "Slowdown": "Cautious/Peak environment",
            "Contraction": "Bearish macro environment",
            "Recovery": "Improving macro environment"
        }
        pe['interp_overall'].set_text(f"Overall:\n{overall_map.get(curr_quad, 'Neutral')}")

        prev_x, prev_y = curr_x, curr_y
        if len(df_slice) > 1:
            prev_x = df_slice.iloc[-2]['X']
            prev_y = df_slice.iloc[-2]['Y']

        mom_diff = curr_y - prev_y
        mom_str = ("Positive (Accelerating)" if mom_diff > 0
                   else ("Negative (Decelerating)" if mom_diff < 0 else "Neutral"))
        pe['interp_mom'].set_text(f"Momentum:\n{mom_str}")

        pe['read_health'].set_text(f"Health:\n{curr_x:.2f}")
        pe['read_mom'].set_text(f"Momentum:\n{curr_y:.2f}")

        dist_center = np.sqrt((curr_x - c) ** 2 + (curr_y - c) ** 2)
        pe['read_dist'].set_text(f"Distance from Center:\n{dist_center:.2f}")

        # Direction
        dx = curr_x - prev_x
        dy = curr_y - prev_y
        if dx == 0 and dy == 0:
            dir_sym = "Neutral"
        else:
            angle = np.degrees(np.arctan2(dy, dx))
            if angle < 0:
                angle += 360
            if 22.5 <= angle < 67.5: dir_sym = "↗ Northeast"
            elif 67.5 <= angle < 112.5: dir_sym = "↑ North"
            elif 112.5 <= angle < 157.5: dir_sym = "↖ Northwest"
            elif 157.5 <= angle < 202.5: dir_sym = "← West"
            elif 202.5 <= angle < 247.5: dir_sym = "↙ Southwest"
            elif 247.5 <= angle < 292.5: dir_sym = "↓ South"
            elif 292.5 <= angle < 337.5: dir_sym = "↘ Southeast"
            else: dir_sym = "→ East"

        pe['read_dir'].set_text(f"Direction:\n{dir_sym}")

        # Macro Drivers
        try:
            from ..analytics.macro_intelligence_engine import MacroIntelligenceEngine
        except ImportError:
            from analytics.macro_intelligence_engine import MacroIntelligenceEngine
        
        macro_contrib = MacroIntelligenceEngine.assign_contribution(df, idx)
        
        for name, d in macro_contrib['evaluations'].items():
            if f'driver_{name}_line1' in pe:
                line1 = pe[f'driver_{name}_line1']
                val = pe[f'driver_{name}_val']
                line2 = pe[f'driver_{name}_line2']
                pct = pe[f'driver_{name}_pct']
                
                display_name = name if name != 'Yield Spread' else 'Yield Curve'
                if d['state'] != 'Unknown':
                    yoy_val = d.get('yoy_value', np.nan)
                    if name in ['CPI'] and not pd.isna(yoy_val):
                        raw_str = f"{yoy_val:.2f}%"
                    elif name in ['Yield 10Y', 'Yield Short', 'Yield Spread', 'Real Policy Rate']:
                        raw_str = f"{d['raw_value']:.2f}%"
                    else:
                        raw_str = f"{d['raw_value']:.2f}"
                        
                    line1.set_text(f"{display_name}")
                    val.set_text(raw_str)
                    
                    if d['trend'] == 'Improving':
                        t_sym = '▲'
                    elif d['trend'] == 'Weakening':
                        t_sym = '▼'
                    else:
                        t_sym = '►'
                        
                    line2.set_text(f"{t_sym} {d['trend']}")
                    pct.set_text(d['percentile'])
                    
                    if d['level'] == 'Positive':
                        color = 'darkgreen'
                    elif d['level'] == 'Negative':
                        color = 'darkred'
                    else:
                        color = 'darkgoldenrod'
                        
                    line1.set_color(color)
                    val.set_color(color)
                    line2.set_color(color)
                else:
                    line1.set_text(f"{display_name}")
                    val.set_text("N/A")
                    line2.set_text("--")
                    pct.set_text("N/A")
                    line1.set_color('#333333')
                    val.set_color('#333333')
                    line2.set_color('#666666')
                    
        # Forecast and Scenarios
        try:
            from ..analytics import historical_analogues
            from ..analytics import transition_matrix as tm_mod
            from ..analytics import forecasting_engine as fe_mod
            from ..analytics import scenario_engine as se_mod
            from ..research import report_data as rd
        except ImportError:
            from analytics import historical_analogues
            from analytics import transition_matrix as tm_mod
            from analytics import forecasting_engine as fe_mod
            from analytics import scenario_engine as se_mod
            from research import report_data as rd

        # Minimal extraction for analogues
        temp_data = {'quadrant': curr_row['Quadrant']}
        analogues = historical_analogues.generate_analogues(df, idx, temp_data, self.market_series)
        forecast_result = fe_mod.ForecastingEngine.project(df, idx, config, analogues, macro_contrib)
        
        if 'fc_base' in pe:
            trans_matrix = tm_mod.compute_transition_matrix(df_slice)
            scenarios = se_mod.ScenarioEngine.generate_scenarios(forecast_result, trans_matrix, analogues, curr_row['Quadrant'], config)
            
            base_sc = next((s for s in scenarios if s['name'] == 'Base'), None)
            bull_sc = next((s for s in scenarios if s['name'] == 'Bull'), None)
            bear_sc = next((s for s in scenarios if s['name'] == 'Bear'), None)
            
            pe['fc_base'].set_text(f"Base: {base_sc['projected_quadrant_6m'] if base_sc else '--'} ({base_sc['probability'] if base_sc else 0:.0f}%)")
            pe['fc_bull'].set_text(f"Bull: {bull_sc['projected_quadrant_6m'] if bull_sc else '--'} ({bull_sc['probability'] if bull_sc else 0:.0f}%)")
            pe['fc_bear'].set_text(f"Bear: {bear_sc['projected_quadrant_6m'] if bear_sc else '--'} ({bear_sc['probability'] if bear_sc else 0:.0f}%)")
            
        # Draw Forecast Line Overlay
        if self.chk_forecast.get_status()[0] and 'projected_path' in forecast_result:
            path = forecast_result['projected_path']
            # Prepend current point to connect
            fc_x = [curr_x] + [p[0] for p in path]
            fc_y = [curr_y] + [p[1] for p in path]
            self.forecast_line.set_data(fc_x, fc_y)
            self.forecast_line.set_visible(True)
            
            if self.forecast_poly:
                self.forecast_poly.remove()
                self.forecast_poly = None
                
            # Confidence band
            residual_std = forecast_result.get('residual_std', {'x': 1.0, 'y': 1.0})
            sigma = 1.0
            upper_x, upper_y, lower_x, lower_y = [], [], [], []
            for i in range(len(fc_x)):
                scale = np.sqrt(max(1, i))
                upper_x.append(fc_x[i] + sigma * residual_std['x'] * scale)
                lower_x.append(fc_x[i] - sigma * residual_std['x'] * scale)
                upper_y.append(fc_y[i] + sigma * residual_std['y'] * scale)
                lower_y.append(fc_y[i] - sigma * residual_std['y'] * scale)
                
            from matplotlib.patches import Polygon
            verts = list(zip(upper_x, upper_y)) + list(zip(lower_x[::-1], lower_y[::-1]))
            self.forecast_poly = Polygon(verts, facecolor='#dc3545', alpha=0.15, zorder=4)
            self.ax.add_patch(self.forecast_poly)
        else:
            self.forecast_line.set_visible(False)
            if self.forecast_poly:
                self.forecast_poly.remove()
                self.forecast_poly = None

        # Market Context
        if 'market_state' in pe:
            m_state = pe['market_state']
            h = m_state['horizon']
            prev_i = idx - h if idx >= h else 0

            for name, series_info in self.market_series.items():
                texts = pe['market_texts'][name]
                if name not in m_state['selected']:
                    texts['name'].set_visible(False)
                    texts['val'].set_visible(False)
                    texts['chg'].set_visible(False)
                    continue

                texts['name'].set_visible(True)
                texts['val'].set_visible(True)
                texts['chg'].set_visible(True)

                cur_val = df[name].iloc[idx]
                prev_val = df[name].iloc[prev_i]
                fmt_str = series_info['format']

                if pd.isna(cur_val):
                    texts['val'].set_text("N/A")
                    texts['chg'].set_text("N/A")
                    texts['chg'].set_color('gray')
                else:
                    texts['val'].set_text(fmt_str.format(cur_val))
                    if pd.isna(prev_val) or prev_i == idx:
                        texts['chg'].set_text("--")
                        texts['chg'].set_color('gray')
                    else:
                        if 'Yield' in name:
                            diff = (cur_val - prev_val) * 100
                            txt = f"{diff:+.0f} bps"
                            clr = '#28a745' if diff > 0 else '#dc3545'
                        else:
                            pct = (cur_val - prev_val) / prev_val * 100
                            txt = f"{pct:+.2f}%"
                            clr = '#28a745' if pct > 0 else '#dc3545'
                        texts['chg'].set_text(txt)
                        texts['chg'].set_color(clr)

        # Tail dots and spline
        if show_tails and len(df_slice) > 1:
            dots_x = df_slice['X'].values[:-1]
            dots_y = df_slice['Y'].values[:-1]
            pe['tail_dots'].set_offsets(np.c_[dots_x, dots_y])

            n_dots = len(dots_x)
            colors = np.zeros((n_dots, 4))
            colors[:, :3] = 0.4
            colors[:, 3] = np.linspace(0.15, 0.7, n_dots)
            pe['tail_dots'].set_facecolors(colors)
            pe['tail_dots'].set_edgecolors(colors)

            mask = (self.spline_data['t'] >= start_idx) & (self.spline_data['t'] <= idx)
            s_slice = self.spline_data[mask]

            sx, sy = s_slice['X'].values, s_slice['Y'].values
            pts = np.array([sx, sy]).T.reshape(-1, 1, 2)
            segments = np.concatenate([pts[:-1], pts[1:]], axis=1)

            pe['lc'].set_segments(segments)

            n_segs = len(segments)
            line_colors = np.zeros((n_segs, 4))
            line_colors[:, :3] = 0.25
            line_colors[:, 3] = np.linspace(0.1, 0.9, n_segs)
            pe['lc'].set_color(line_colors)
        else:
            pe['tail_dots'].set_offsets(np.empty((0, 2)))
            pe['lc'].set_segments([])

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _wire_callbacks(self):
        fig = self.fig
        df = self.df
        config = self.config
        pe = self.plot_elements

        def update_plot(val):
            self.state['current_frame'] = int(val)
            self.draw_frame(self.state['current_frame'])
            fig.canvas.draw_idle()

        self.slider.on_changed(update_plot)

        def animation_step(frame):
            if self.state['is_playing']:
                self.state['current_frame'] += 1
                if self.state['current_frame'] > self.max_frames:
                    self.state['current_frame'] = 0
                self.slider.set_val(self.state['current_frame'])

        self.anim = FuncAnimation(fig, animation_step, interval=200, cache_frame_data=False)
        self.anim.event_source.stop()

        def play(event):
            if not self.state['is_playing']:
                self.state['is_playing'] = True
                self.anim.event_source.start()

        def pause(event):
            if self.state['is_playing']:
                self.state['is_playing'] = False
                self.anim.event_source.stop()

        def reset(event):
            pause(None)
            self.slider.set_val(0)

        def set_speed(label):
            speed_map = {'1x': 200, '2x': 100, '3x': 50}
            self.anim.event_source.interval = speed_map[label]
            for l, btn in [('1x', self.btn_1x), ('2x', self.btn_2x), ('3x', self.btn_3x)]:
                if label == l:
                    btn.color = '#1f497d'
                    btn.ax.set_facecolor('#1f497d')
                    btn.label.set_color('#ffffff')
                else:
                    btn.color = '#ffffff'
                    btn.ax.set_facecolor('#ffffff')
                    btn.label.set_color('#495057')
            fig.canvas.draw_idle()

        def toggle_tails(label):
            is_on = self.chk_tails.get_status()[0]
            pe['tail_dots'].set_visible(is_on)
            pe['lc'].set_visible(is_on)
            fig.canvas.draw_idle()

        def toggle_labels(label):
            is_on = self.chk_labels.get_status()[0]
            pe['current_label'].set_visible(is_on)
            fig.canvas.draw_idle()

        def toggle_market(label):
            is_on = self.chk_market.get_status()[0]
            pe['ax_market'].set_visible(is_on)
            pe['ax_market_cfg'].set_visible(is_on)
            pe['ax_market_mode'].set_visible(is_on)
            pe['market_header'].set_visible(is_on)
            pe['market_sep'].set_visible(is_on)
            self._update_market_layout()
            fig.canvas.draw_idle()

        def toggle_forecast(label):
            self.draw_frame(self.state['current_frame'])
            fig.canvas.draw_idle()

        self.btn_play.on_clicked(play)
        self.btn_pause.on_clicked(pause)
        self.btn_reset.on_clicked(reset)

        self.btn_1x.on_clicked(lambda e: set_speed('1x'))
        self.btn_2x.on_clicked(lambda e: set_speed('2x'))
        self.btn_3x.on_clicked(lambda e: set_speed('3x'))
        set_speed('1x')  # Initialize active visual state

        self.chk_tails.on_clicked(toggle_tails)
        self.chk_labels.on_clicked(toggle_labels)
        self.chk_market.on_clicked(toggle_market)
        self.chk_forecast.on_clicked(toggle_forecast)

        # Scroll
        def on_scroll(event):
            if not self.chk_market.get_status()[0]:
                return
            if event.inaxes == pe['ax_market']:
                m_state = pe['market_state']
                step = 0.08
                if event.button == 'up':
                    m_state['scroll_y'] -= step
                elif event.button == 'down':
                    m_state['scroll_y'] += step

                num_sel = len(m_state['selected'])
                max_y = max(0, (num_sel * 0.16) - 1.0)
                m_state['scroll_y'] = max(0, min(m_state['scroll_y'], max_y))

                sy = -m_state['scroll_y']
                pe['ax_market'].set_ylim(sy, sy + 1)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect('scroll_event', on_scroll)

        # Market config popup
        def show_market_config(event):
            m_state = pe['market_state']
            if m_state['menu_fig'] and plt.fignum_exists(m_state['menu_fig'].number):
                m_state['menu_fig'].canvas.manager.window.lift()
                return

            cfig = plt.figure(figsize=(3, 5))
            cfig.canvas.manager.set_window_title("Market Selection")
            ax_cb = cfig.add_axes([0.1, 0.1, 0.8, 0.8])
            ax_cb.axis('off')

            labels = list(self.market_series.keys())
            states = [l in m_state['selected'] for l in labels]

            cb = CheckButtons(ax_cb, labels, states)

            def on_cb(label):
                if label in m_state['selected']:
                    m_state['selected'].remove(label)
                else:
                    m_state['selected'].append(label)
                self._update_market_layout()
                self.draw_frame(self.slider.val)
                fig.canvas.draw_idle()

            cb.on_clicked(on_cb)
            cfig.cb = cb
            m_state['menu_fig'] = cfig
            plt.show(block=False)

        self.widgets['btn_market_cfg'].on_clicked(show_market_config)

        # Market mode popup
        def show_market_mode(event):
            m_state = pe['market_state']
            if m_state['mode_fig'] and plt.fignum_exists(m_state['mode_fig'].number):
                m_state['mode_fig'].canvas.manager.window.lift()
                return

            mfig = plt.figure(figsize=(2.5, 3))
            mfig.canvas.manager.set_window_title("Horizon")
            ax_rb = mfig.add_axes([0.1, 0.1, 0.8, 0.8])
            ax_rb.axis('off')

            horizons = {'1M Change': 1, '3M Change': 3, '6M Change': 6, '12M Change': 12}
            labels = list(horizons.keys())
            rb_idx = list(horizons.values()).index(m_state['horizon'])

            rb = RadioButtons(ax_rb, labels, active=rb_idx)

            def on_rb(label):
                m_state['horizon'] = horizons[label]
                self.widgets['btn_market_mode'].label.set_text(f"{label[:2]} ▼")
                self.draw_frame(self.slider.val)
                fig.canvas.draw_idle()
                plt.close(mfig)

            rb.on_clicked(on_rb)
            mfig.rb = rb
            m_state['mode_fig'] = mfig
            plt.show(block=False)

        self.widgets['btn_market_mode'].on_clicked(show_market_mode)

        # Keyboard shortcuts
        def on_key_press(event):
            if not event.key:
                return
            key = event.key.lower()
            if key == ' ':
                if self.state['is_playing']:
                    pause(None)
                else:
                    play(None)
            elif key == 'left':
                pause(None)
                self.slider.set_val(max(0, self.state['current_frame'] - 1))
            elif key == 'right':
                pause(None)
                self.slider.set_val(min(self.max_frames, self.state['current_frame'] + 1))
            elif key == 'home':
                pause(None)
                self.slider.set_val(0)
            elif key == 'end':
                pause(None)
                self.slider.set_val(self.max_frames)
            elif key == 'r':
                reset(None)

        fig.canvas.mpl_connect('key_press_event', on_key_press)

        # Help
        def show_help(event):
            help_fig = plt.figure(figsize=(4.5, 5.0))
            help_fig.canvas.manager.set_window_title("Help & Shortcuts")
            help_fig.patch.set_facecolor('#f8f9fa')

            help_text = f"""{config['name']} - Macro Intelligence Platform v{config['version']}

A quantitative macroeconomic research tool that normalizes leading indicators into 
orthogonal health (X) and momentum (Y) vectors to mathematically identify business cycle regimes.

Keyboard Shortcuts:
Space  →  Play / Pause
←      →  Previous Month
→      →  Next Month
Home   →  First Observation
End    →  Latest Observation
R      →  Reset

Usage:
The chart tracks the relationship between economic Health
(Z-Score) and Momentum (Delta Z-Score). 

The path transitions through four phases: 
• Recovery (Blue)
• Expansion (Green) 
• Slowdown (Yellow) 
• Contraction (Red)
"""
            help_fig.text(0.05, 0.95, help_text, fontsize=10, linespacing=1.6,
                          va='top', ha='left', color='#333333')
            plt.show()

        self.btn_help.on_clicked(show_help)

        # Open folder
        def open_export_folder(event):
            export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '..', '..', 'Exports')
            os.makedirs(export_dir, exist_ok=True)
            os.startfile(os.path.abspath(export_dir))

        self.btn_open.on_clicked(open_export_folder)

        # Status messages
        def show_status_msg(msg, show_btn=False):
            pe['status_label'].set_text(msg)
            pe['status_label'].set_fontweight('bold')
            pe['status_label'].set_color('white')
            pe['status_label'].set_bbox(dict(facecolor='#28a745', edgecolor='#1e7e34',
                                             boxstyle='round,pad=0.3'))
            if show_btn:
                pe['ax_open'].set_visible(True)
            fig.canvas.draw_idle()

            def restore():
                pe['status_label'].set_text(pe['default_status'])
                pe['status_label'].set_fontweight('normal')
                pe['status_label'].set_color('dimgray')
                pe['status_label'].set_bbox(dict(facecolor='none', edgecolor='none'))
                pe['ax_open'].set_visible(False)
                fig.canvas.draw_idle()

            t = fig.canvas.new_timer(interval=10000)
            t.single_shot = True
            t.add_callback(restore)
            t.start()
            pe['active_timer'] = t

        # Export
        def export_data(fmt):
            export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '..', '..', 'Exports')
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

            if fmt.startswith('fig_'):
                ext = fmt.split('_')[1]
                filename = f"BusinessCycle_Figure_{timestamp}.{ext}"
                filepath = os.path.join(export_dir, filename)
                try:
                    for ax_ctrl in pe['control_axes']:
                        ax_ctrl.set_visible(False)
                    for bg_el in pe['control_bg_elements']:
                        bg_el.set_visible(False)

                    old_text = pe['status_label'].get_text()
                    old_color = pe['status_label'].get_color()
                    old_weight = pe['status_label'].get_fontweight()

                    pe['status_label'].set_text(pe['default_status'])
                    pe['status_label'].set_fontweight('normal')
                    pe['status_label'].set_color('dimgray')
                    pe['status_label'].set_bbox(dict(facecolor='none', edgecolor='none'))

                    fig.savefig(filepath, dpi=300, bbox_inches='tight')

                    for ax_ctrl in pe['control_axes']:
                        ax_ctrl.set_visible(True)
                    for bg_el in pe['control_bg_elements']:
                        bg_el.set_visible(True)
                    pe['status_label'].set_text(old_text)
                    pe['status_label'].set_color(old_color)
                    pe['status_label'].set_fontweight(old_weight)

                    show_status_msg(f"✓ Saved: Exports\\{filename}", show_btn=True)
                except Exception as e:
                    for ax_ctrl in pe['control_axes']:
                        ax_ctrl.set_visible(True)
                    for bg_el in pe['control_bg_elements']:
                        bg_el.set_visible(True)
                    show_status_msg(f"Export Error: {e}", show_btn=False)

            elif fmt == 'pdf_report':
                filename = f"Macro_Brief_{timestamp}.pdf"
                filepath = os.path.join(export_dir, filename)
                try:
                    try:
                        from ..research import report_data as rd
                        from ..analytics import cycle_statistics
                        from ..analytics import insights as insights_mod
                        from ..analytics import market_insights as mi_mod
                        from ..research import narrative as narrative_mod
                        from ..analytics import historical_analogues
                        from ..analytics import deltas as deltas_mod
                        from ..analytics import transition_matrix as tm_mod
                        from ..analytics import forecasting_engine as fe_mod
                        from ..analytics import scenario_engine as se_mod
                        from ..research import pdf as pdf_mod
                    except ImportError:
                        from research import report_data as rd
                        from analytics import cycle_statistics
                        from analytics import insights as insights_mod
                        from analytics import market_insights as mi_mod
                        from research import narrative as narrative_mod
                        from analytics import historical_analogues
                        from analytics import deltas as deltas_mod
                        from analytics import transition_matrix as tm_mod
                        from analytics import forecasting_engine as fe_mod
                        from analytics import scenario_engine as se_mod
                        from research import pdf as pdf_mod

                    temp_fig = os.path.join(export_dir, f"temp_{timestamp}.png")
                    for ax_ctrl in pe['control_axes']:
                        ax_ctrl.set_visible(False)
                    for bg_el in pe['control_bg_elements']:
                        bg_el.set_visible(False)

                    old_text = pe['status_label'].get_text()
                    old_color = pe['status_label'].get_color()
                    old_weight = pe['status_label'].get_fontweight()

                    pe['status_label'].set_text(pe['default_status'])
                    pe['status_label'].set_fontweight('normal')
                    pe['status_label'].set_color('dimgray')
                    pe['status_label'].set_bbox(dict(facecolor='none', edgecolor='none'))

                    fig.savefig(temp_fig, dpi=300, bbox_inches='tight')

                    for ax_ctrl in pe['control_axes']:
                        ax_ctrl.set_visible(True)
                    for bg_el in pe['control_bg_elements']:
                        bg_el.set_visible(True)
                    pe['status_label'].set_text(old_text)
                    pe['status_label'].set_color(old_color)
                    pe['status_label'].set_fontweight(old_weight)

                    current_idx = int(self.slider.val)
                    df_sliced = df.iloc[:current_idx + 1]

                    data = rd.extract_report_data(df, config, pe, current_idx, self.market_series)
                    analysis = cycle_statistics.compute_statistics(df_sliced, data)
                    ins = insights_mod.generate_insights(data, analysis)
                    market_ins = mi_mod.generate_market_insights(data)
                    analogues = historical_analogues.generate_analogues(
                        df, current_idx, data, self.market_series
                    )
                    
                    # --- Phase 3 Engines ---
                    trans_matrix = tm_mod.compute_transition_matrix(df_sliced)
                    forecast_result = fe_mod.ForecastingEngine.project(
                        df, current_idx, config, analogues, data.get('macro_contrib')
                    )
                    scenarios = se_mod.ScenarioEngine.generate_scenarios(
                        forecast_result, trans_matrix, analogues, data['quadrant'], config
                    )
                    
                    data['transition_matrix'] = trans_matrix
                    data['forecast'] = forecast_result
                    data['scenarios'] = scenarios
                    # -----------------------

                    deltas = deltas_mod.calculate_deltas(
                        df, current_idx, config, pe, self.market_series,
                        data, analysis, ins
                    )
                    narrative = narrative_mod.generate_narrative(
                        data, analysis, ins, market_ins, analogues
                    )
                    pdf_mod.build_pdf_report(
                        data, analysis, ins, market_ins, narrative,
                        analogues, deltas, temp_fig, filepath,
                        self.data_metadata
                    )

                    if os.path.exists(temp_fig):
                        os.remove(temp_fig)

                    show_status_msg(f"✓ Saved: Exports\\{filename}", show_btn=True)
                except Exception as e:
                    for ax_ctrl in pe['control_axes']:
                        ax_ctrl.set_visible(True)
                    for bg_el in pe['control_bg_elements']:
                        bg_el.set_visible(True)
                    show_status_msg(f"Export Error: {e}", show_btn=False)

            elif fmt == 'screen_png':
                filename = f"BusinessCycle_Screenshot_{timestamp}.png"
                filepath = os.path.join(export_dir, filename)
                try:
                    fig.savefig(filepath, dpi=300, bbox_inches='tight')
                    show_status_msg(f"✓ Saved: Exports\\{filename}", show_btn=True)
                except Exception as e:
                    show_status_msg(f"Export Error: {e}", show_btn=False)

            elif fmt == 'csv':
                filename = f"BusinessCycle_Data_{timestamp}.csv"
                filepath = os.path.join(export_dir, filename)
                try:
                    c = config['center']
                    out_df = df.copy()
                    out_df['Distance from Center'] = np.sqrt(
                        (out_df['X'] - c) ** 2 + (out_df['Y'] - c) ** 2
                    )

                    dirs = []
                    for i in range(len(out_df)):
                        if i == 0:
                            dirs.append('--')
                        else:
                            ddx = out_df['X'].iloc[i] - out_df['X'].iloc[i - 1]
                            ddy = out_df['Y'].iloc[i] - out_df['Y'].iloc[i - 1]
                            angle = math.degrees(math.atan2(ddy, ddx))
                            if angle < 0:
                                angle += 360

                            if angle < 22.5 or angle >= 337.5: d = 'East'
                            elif angle < 67.5: d = 'Northeast'
                            elif angle < 112.5: d = 'North'
                            elif angle < 157.5: d = 'Northwest'
                            elif angle < 202.5: d = 'West'
                            elif angle < 247.5: d = 'Southwest'
                            elif angle < 292.5: d = 'South'
                            else: d = 'Southeast'
                            dirs.append(d)
                    out_df['Direction'] = dirs

                    export_csv = pd.DataFrame({
                        'Date': out_df.index.strftime('%Y-%m-%d'),
                        'Raw Indicator Value': out_df['PMI'],
                        'Health (X)': out_df['X'].round(4),
                        'Momentum (Y)': out_df['Y'].round(4),
                        'Quadrant': out_df['Quadrant'],
                        'Distance from Center': out_df['Distance from Center'].round(4),
                        'Direction': out_df['Direction']
                    })
                    export_csv.to_csv(filepath, index=False)
                    show_status_msg(f"✓ Saved: Exports\\{filename}", show_btn=True)
                except Exception as e:
                    show_status_msg(f"Export Error: {e}", show_btn=False)

        def show_export_menu(event):
            if 'fig' in self.export_menu and plt.fignum_exists(self.export_menu['fig'].number):
                self.export_menu['fig'].canvas.manager.window.lift()
                return

            efig = plt.figure(figsize=(3.0, 5.0))
            efig.canvas.manager.set_window_title("Export")
            efig.patch.set_facecolor('#f8f9fa')
            self.export_menu['fig'] = efig

            ax_fig_png = efig.add_axes([0.15, 0.82, 0.7, 0.12])
            btn_fig_png = Button(ax_fig_png, 'Figure (PNG)', color='#e9ecef', hovercolor='#dee2e6')

            ax_fig_svg = efig.add_axes([0.15, 0.68, 0.7, 0.12])
            btn_fig_svg = Button(ax_fig_svg, 'Figure (SVG)', color='#e9ecef', hovercolor='#dee2e6')

            ax_csv = efig.add_axes([0.15, 0.54, 0.7, 0.12])
            btn_csv = Button(ax_csv, 'Data (CSV)', color='#e9ecef', hovercolor='#dee2e6')

            efig.add_artist(plt.Line2D([0.1, 0.9], [0.50, 0.50], color='lightgray'))

            ax_pdf = efig.add_axes([0.15, 0.36, 0.7, 0.12])
            btn_pdf = Button(ax_pdf, 'Macro Brief (PDF)', color='#e9ecef', hovercolor='#dee2e6')

            efig.add_artist(plt.Line2D([0.1, 0.9], [0.32, 0.32], color='lightgray'))

            ax_screen = efig.add_axes([0.15, 0.18, 0.7, 0.12])
            btn_screen = Button(ax_screen, 'Screenshot (PNG)', color='#e9ecef', hovercolor='#dee2e6')

            self.export_menu['btns'] = [btn_fig_png, btn_fig_svg, btn_csv, btn_pdf, btn_screen]

            def on_export(fmt):
                plt.close(efig)
                export_data(fmt)

            btn_fig_png.on_clicked(lambda e: on_export('fig_png'))
            btn_fig_svg.on_clicked(lambda e: on_export('fig_svg'))
            btn_csv.on_clicked(lambda e: on_export('csv'))
            btn_pdf.on_clicked(lambda e: on_export('pdf_report'))
            btn_screen.on_clicked(lambda e: on_export('screen_png'))

            efig.canvas.draw()
            plt.show(block=False)

        self.btn_export.on_clicked(show_export_menu)

        # Initialize to latest frame
        self.slider.set_val(self.max_frames)

        # Startup timer to restore status bar
        def restore_status():
            pe['status_label'].set_text(pe['default_status'])
            pe['status_label'].set_fontweight('normal')
            pe['status_label'].set_color('dimgray')
            pe['status_label'].set_bbox(dict(facecolor='none', edgecolor='none'))
            fig.canvas.draw_idle()

        startup_timer = fig.canvas.new_timer(interval=10000)
        startup_timer.single_shot = True
        startup_timer.add_callback(restore_status)
        startup_timer.start()
        pe['startup_timer'] = startup_timer

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    def run(self):
        """Start the matplotlib event loop."""
        plt.show()
