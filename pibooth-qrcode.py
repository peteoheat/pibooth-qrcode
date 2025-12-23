# -*- coding: utf-8 -*-
"""Pibooth plugin to display a QR Code on the screen during idle time.

This module is the original pibooth-qrcode plugin updated to optionally save
the generated QR image. The saved QR will be written into the directory
configured in the [GENERAL] section 'directory' by default. If the optional
[qrcode] setting 'save_path' is present, that path is used instead.

This variant runs the QR generation and optional save during the processing loop
hook named state_processing_do (as requested).

New config keys under [QRCODE]:
- save (bool)        : whether to save the QR image (default False)
- suffix (string)    : filename suffix to append before extension (default _qrcode)
- ext (string)       : file extension for saved QR image (default png)
- save_path (string) : optional path to save QR images; if set overrides GENERAL.directory
"""

from __future__ import annotations

try:
    import qrcode
except ImportError:
    qrcode = None

import os
import logging

import pygame
import pibooth
from pibooth.view.background import multiline_text_to_surfaces

__version__ = '1.0.5'

SECTION = 'QRCODE'
LOCATIONS = ['topleft', 'topright', 'bottomleft', 'bottomright',
             'midtop-left', 'midtop-right', 'midbottom-left', 'midbottom-right']

logger = logging.getLogger(__name__)


@pibooth.hookimpl
def pibooth_configure(cfg):
    """Declare the new configuration options"""
    cfg.add_option(SECTION, 'prefix_url', "{url}",
                   "URL which may be composed of variables: {picture}, {count}, {url}")
    cfg.add_option(SECTION, 'foreground', (255, 255, 255), "Foreground color", "Color", (255, 255, 255))
    cfg.add_option(SECTION, 'background', (0, 0, 0), "Background color", "Background color", (0, 0, 0))
    cfg.add_option(SECTION, 'side_text', "", "Optional text displayed close to the QR code", "Side text", "")
    cfg.add_option(SECTION, 'offset', (20, 40), "Offset (x, y) from location")
    cfg.add_option(SECTION, 'wait_location', "bottomleft",
                   "Location on 'wait' state: {}".format(', '.join(LOCATIONS)),
                   "Location on wait screen", LOCATIONS)
    cfg.add_option(SECTION, 'print_location', "bottomright",
                   "Location on 'print' state: {}".format(', '.join(LOCATIONS)),
                   "Location on print screen", LOCATIONS)

    # New options for saving the QR image
    cfg.add_option(SECTION, 'save', False, "Save the generated QR image next to the picture file", None, False)
    cfg.add_option(SECTION, 'suffix', "_qrcode", "Suffix to add to picture basename for saved QR file", None, "_qrcode")
    cfg.add_option(SECTION, 'ext', "png", "Extension for saved QR file", None, "png")
    cfg.add_option(SECTION, 'save_path', "", "Optional directory to save QR images (overrides GENERAL.directory)", None, "")


def get_qrcode_rect(win_rect, qrcode_image, location, offset):
    sublocation = ''
    if '-' in location:
        location, sublocation = location.split('-')
    pos = list(getattr(win_rect, location))
    if 'top' in location:
        pos[1] += offset[1]
    else:
        pos[1] -= offset[1]
    if 'left' in location:
        pos[0] += offset[0]
    else:
        pos[0] -= offset[0]
    if 'mid' in location:
        if 'left' in sublocation:
            pos[0] -= qrcode_image.get_size()[0] // 2
        else:
            pos[0] += (qrcode_image.get_size()[0] // 2 + 2 * offset[0])
    qr_rect = qrcode_image.get_rect(**{location: pos})
    return qr_rect


def get_text_rect(win_rect, qrcode_rect, location, margin=10):
    text_rect = pygame.Rect(0, 0, win_rect.width // 6, qrcode_rect.height)
    sublocation = ''
    if '-' in location:
        location, sublocation = location.split('-')
    text_rect.top = qrcode_rect.top
    if 'left' in location:
        text_rect.left = qrcode_rect.right + margin
    else:
        text_rect.right = qrcode_rect.left - margin
    if 'mid' in location:
        if 'left' in sublocation:
            text_rect.right = qrcode_rect.left - margin
        else:
            text_rect.left = qrcode_rect.right + margin
    return text_rect


@pibooth.hookimpl
def pibooth_startup(cfg):
    """Check the coherence of options."""
    for state in ('wait', 'print'):
        if cfg.get(SECTION, '{}_location'.format(state)) not in LOCATIONS:
            raise ValueError("Unknown QR code location on '{}' state '{}'".format(
                state, cfg.get(SECTION, '{}_location'.format(state))))


def _determine_save_directory(cfg, picture_filename):
    """
    Determine where to save QR images:
    - If QRCODE.save_path is set (non-empty), use it (interpreted as absolute or relative path).
    - Otherwise use GENERAL.directory from config.
    - If neither is available, fall back to the directory of the picture_filename.
    Returns an absolute path.
    """
    # 1) explicit QRCODE.save_path
    save_path = cfg.get(SECTION, 'save_path') or ""
    if save_path:
        save_dir = os.path.expanduser(save_path)
    else:
        # 2) GENERAL.directory
        try:
            general_dir = cfg.get('GENERAL', 'directory')
        except Exception:
            general_dir = ""
        if general_dir:
            save_dir = os.path.expanduser(general_dir)
        else:
            # 3) fallback to picture file directory
            if picture_filename:
                save_dir = os.path.dirname(os.path.abspath(picture_filename))
            else:
                save_dir = os.getcwd()
    # Ensure absolute path
    if not os.path.isabs(save_dir):
        save_dir = os.path.abspath(save_dir)
    return save_dir


@pibooth.hookimpl(trylast=True)
def state_processing_do(cfg, app):
    """
    Run during processing loop (state_processing_do).
    Generate the QR Code, store it in the application and optionally save it to the configured directory.
    """
    if qrcode is None:
        raise ModuleNotFoundError("No module named 'qrcode'")

    try:
        # build QR code
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=3, border=1)

        url_vars = {
            'picture': app.picture_filename,
            'count': app.count,
            'url': getattr(app, 'previous_picture_url', None) or ''
        }

        qr_text = cfg.get(SECTION, 'prefix_url').format(**url_vars)
        qr.add_data(qr_text)
        qr.make(fit=True)

        qrcode_fill_color = '#%02x%02x%02x' % cfg.gettyped("QRCODE", 'foreground')
        qrcode_background_color = '#%02x%02x%02x' % cfg.gettyped("QRCODE", 'background')
        image = qr.make_image(fill_color=qrcode_fill_color, back_color=qrcode_background_color)

        # Keep the pygame-compatible surface for display
        try:
            app.previous_qr = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        except Exception:
            # Fallback if direct conversion fails: create a pygame surface via conversion
            pil_mode = image.mode
            if pil_mode not in ('RGB', 'RGBA'):
                image = image.convert('RGBA')
            string = image.tobytes()
            app.previous_qr = pygame.image.fromstring(string, image.size, 'RGBA')

        # Optional: save the QR image to configured directory
        save_enabled = cfg.get(SECTION, 'save')
        if save_enabled:
            picture_filename = app.picture_filename
            # Prepare basename for saved file. Use picture basename if available, otherwise a count-based name.
            if picture_filename:
                base_name = os.path.splitext(os.path.basename(picture_filename))[0]
            else:
                base_name = f"picture_{getattr(app, 'count', '0')}"

            suffix = cfg.get(SECTION, 'suffix') or "_qrcode"
            ext = (cfg.get(SECTION, 'ext') or "png").lstrip('.')
            save_dir = _determine_save_directory(cfg, picture_filename)

            # Ensure directory exists
            try:
                os.makedirs(save_dir, exist_ok=True)
            except Exception:
                logger.exception("pibooth-qrcode: could not create save directory %s", save_dir)

            qr_filename = f"{base_name}{suffix}.{ext}"
            qr_path = os.path.join(save_dir, qr_filename)

            try:
                img_to_save = image

                # Normalize Pillow image modes for requested extension
                ext_l = ext.lower()
                if hasattr(img_to_save, "mode"):
                    mode = img_to_save.mode
                    if mode == "P":
                        img_to_save = img_to_save.convert("RGBA")
                    if mode == "RGBA" and ext_l in ("jpg", "jpeg"):
                        img_to_save = img_to_save.convert("RGB")
                    elif mode not in ("RGB", "RGBA") and ext_l in ("png", "jpg", "jpeg"):
                        img_to_save = img_to_save.convert("RGB")

                # Save file
                try:
                    img_to_save.save(qr_path)
                    logger.info("pibooth-qrcode: saved QR image to %s", qr_path)
                except Exception:
                    # Try converting to RGBA then saving as fallback
                    try:
                        img2 = image.convert("RGBA")
                        img2.save(qr_path)
                        logger.info("pibooth-qrcode: saved QR image to %s (via RGBA fallback)", qr_path)
                    except Exception as e:
                        logger.exception("pibooth-qrcode: failed saving QR image to %s: %s", qr_path, e)

                # Optionally attach saved path into app metadata if present
                try:
                    if hasattr(app, "picture_metadata") and isinstance(app.picture_metadata, dict) and picture_filename:
                        abs_picture = os.path.abspath(picture_filename)
                        app.picture_metadata.setdefault(abs_picture, {})["qrcode_path"] = os.path.abspath(qr_path)
                except Exception:
                    # Don't let metadata attach failures break flow
                    pass

            except Exception as e:
                logger.exception("pibooth-qrcode: unexpected error while saving QR image: %s", e)

    except Exception:
        logger.exception("pibooth-qrcode: error while generating or saving QR image")


@pibooth.hookimpl
def state_wait_enter(cfg, app, win):
    """Display the QR Code on the wait view."""
    win_rect = win.get_rect()
    location = cfg.get(SECTION, 'wait_location')
    if hasattr(app, 'previous_qr') and app.previous_picture:
        offset = cfg.gettuple(SECTION, 'offset', int, 2)
        app.qr_rect = get_qrcode_rect(win_rect, app.previous_qr, location, offset)
        win.surface.blit(app.previous_qr, app.qr_rect.topleft)
        if cfg.get(SECTION, 'side_text'):
            text_rect = get_text_rect(win_rect, app.qr_rect, location)
            app.qr_texts = multiline_text_to_surfaces(cfg.get(SECTION, 'side_text'),
                                                      cfg.gettyped('WINDOW', 'text_color'),
                                                      text_rect, 'bottom-left')
            for text, rect in app.qr_texts:
                win.surface.blit(text, rect)


@pibooth.hookimpl
def state_wait_do(app, win):
    """Redraw the QR Code because it may have been erased by a screen update (for instance, if a print is done)."""
    if hasattr(app, 'previous_qr') and app.previous_picture:  # Not displayed if no previous capture is deleted
        win.surface.blit(app.previous_qr, app.qr_rect.topleft)
        if hasattr(app, 'qr_texts'):
            for text, rect in app.qr_texts:
                win.surface.blit(text, rect)


@pibooth.hookimpl
def state_print_enter(cfg, app, win):
    """Display the QR Code on the print view."""
    win_rect = win.get_rect()
    offset = cfg.gettuple(SECTION, 'offset', int, 2)
    location = cfg.get(SECTION, 'print_location')
    qrcode_rect = get_qrcode_rect(win_rect, app.previous_qr, location, offset)

    if cfg.get(SECTION, 'side_text'):
        text_rect = get_text_rect(win_rect, qrcode_rect, location)
        texts = multiline_text_to_surfaces(cfg.get(SECTION, 'side_text'),
                                           cfg.gettyped('WINDOW', 'text_color'),
                                           text_rect, 'bottom-left')
        for text, rect in texts:
            win.surface.blit(text, rect)

    win.surface.blit(app.previous_qr, qrcode_rect.topleft)
