use std::io::Cursor;

use image::{
    imageops::{invert, overlay, resize},
    ImageBuffer, ImageOutputFormat, Rgba, RgbaImage,
};
use imageproc::{
    drawing::{draw_filled_circle_mut, draw_filled_rect_mut, draw_text_mut},
    rect::Rect,
};
use rusttype::Font;

use crate::Data;

const BACKGROUND: Rgba<u8> = Rgba([255, 255, 255, 255]);
const FOREGROUND: Rgba<u8> = Rgba([0, 0, 0, 255]);
const HEIGHT: u32 = 34;
const LN_SPACE: u32 = 2;
const SCALE: rusttype::Scale = rusttype::Scale {
    x: HEIGHT as f32,
    y: HEIGHT as f32,
};
const WIDTH: f32 = HEIGHT as f32 * 0.65;
const POS: (u32, u32) = (42, 42);

const RECT_POS: u32 = (POS.1 + (HEIGHT + LN_SPACE) * 4 + LN_SPACE * 2);
const RECT_SIZE: (u32, u32) = (410, 30);

pub fn create_level_image(font: &Font, radius: u32) -> ImageBuffer<Rgba<u8>, Vec<u8>> {
    // let mut image = image::open("assets/winterrankcard.png").unwrap().to_rgba8();
    let mut image = RgbaImage::from_pixel(720, 256, BACKGROUND);
    // let radius = 12;

    ["User:", "Experience:", "Level:", "Rank:"]
        .into_iter()
        .enumerate()
        .for_each(|(i, line)| {
            draw_text_mut(
                &mut image,
                FOREGROUND,
                POS.0 as i32 - 2,
                POS.1 as i32 + ((HEIGHT + LN_SPACE) as usize * i) as i32,
                SCALE,
                font,
                line,
            );
        });
    draw_filled_rect_mut(
        &mut image,
        Rect::at(POS.0 as i32, RECT_POS as i32).of_size(RECT_SIZE.0, RECT_SIZE.1),
        FOREGROUND,
    );
    round(&mut image, (radius, radius, radius, radius));
    image
}

pub async fn level_embed(
    data: &Data,
    username: &str,
    level: &str,
    xp: u32,
    xp_for_next_level: u32,
    rank: String,
    avatar_url: String,
) -> Option<Cursor<Vec<u8>>> {
    let mut image = *data.level_image.clone();
    let font = &data.font;

    let Ok(response) = data.http_client.get(avatar_url.replace("?size=1024", "?size=256")).send().await else {
        return None
    };
    // println!("{response:?}");
    let Ok(avatar) = response.bytes().await else {
        return None
    };
    // println!("{avatar:?}");
    let Ok(mut avatar) = image::load_from_memory(&avatar).map(|x|x.to_rgba8()) else {
        return None
    };
    let size = (189i32, 189i32);
    let midpoint = ((size.0 + size.1) / 4) as i64;
    let mut avatar = resize(
        &avatar,
        size.0 as u32,
        size.1 as u32,
        image::imageops::FilterType::Triangle,
    );
    let midpoint = midpoint as u32;
    round(&mut avatar, (midpoint, midpoint, midpoint, midpoint));
    overlay(&mut image, &avatar, 489, 35);

    [
        ("User:", username, 0),
        ("Experience:", &format!("{xp}/{xp_for_next_level}"), 0),
        ("Level:", level, -2),
        ("Rank:", &format!("#{rank}"), 8),
    ]
    .into_iter()
    .enumerate()
    .for_each(|(i, (oldline, line, offset))| {
        draw_text_mut(
            &mut image,
            FOREGROUND,
            POS.0 as i32 + (WIDTH * oldline.len() as f32 * data.font_width) as i32 + offset + 3,
            POS.1 as i32 + ((HEIGHT + LN_SPACE) as usize * i) as i32,
            SCALE,
            font,
            &line,
        );
    });
    draw_filled_rect_mut(
        &mut image,
        Rect::at(POS.0 as i32 + 2, RECT_POS as i32 + 2).of_size(
            (((RECT_SIZE.0 - 4) as f32 * (xp as f32 / xp_for_next_level as f32)) as u32).max(1),
            RECT_SIZE.1 - 4,
        ),
        BACKGROUND,
    );

    let mut cursor = Cursor::new(Vec::new());
    image.write_to(&mut cursor, ImageOutputFormat::Png);
    Some(cursor)
}

fn round(img: &mut ImageBuffer<Rgba<u8>, Vec<u8>>, radius: (u32, u32, u32, u32)) {
    let (width, height) = img.dimensions();
    assert!(radius.0 + radius.1 <= width);
    assert!(radius.3 + radius.2 <= width);
    assert!(radius.0 + radius.3 <= height);
    assert!(radius.1 + radius.2 <= height);

    // top left
    border_radius(img, radius.0, |x, y| (x - 1, y - 1));
    // top right
    border_radius(img, radius.1, |x, y| (width - x, y - 1));
    // bottom right
    border_radius(img, radius.2, |x, y| (width - x, height - y));
    // bottom left
    border_radius(img, radius.3, |x, y| (x - 1, height - y));
}

fn border_radius(
    img: &mut ImageBuffer<Rgba<u8>, Vec<u8>>,
    r: u32,
    coordinates: impl Fn(u32, u32) -> (u32, u32),
) {
    if r == 0 {
        return;
    }
    let r0 = r;

    // 16x antialiasing: 16x16 grid creates 256 possible shades, great for u8!
    let r = 16 * r;

    let mut x = 0;
    let mut y = r - 1;
    let mut p: i32 = 2 - r as i32;

    // ...

    let mut alpha: u16 = 0;
    let mut skip_draw = true;

    let draw = |img: &mut ImageBuffer<Rgba<u8>, Vec<u8>>, alpha, x, y| {
        debug_assert!((1..=256).contains(&alpha));
        let pixel_alpha = &mut img[coordinates(r0 - x, r0 - y)].0[3];
        *pixel_alpha = ((alpha * *pixel_alpha as u16 + 128) / 256) as u8;
    };

    'l: loop {
        // (comments for bottom_right case:)
        // remove contents below current position
        {
            let i = x / 16;
            for j in y / 16 + 1..r0 {
                img[coordinates(r0 - i, r0 - j)].0[3] = 0;
            }
        }
        // remove contents right of current position mirrored
        {
            let j = x / 16;
            for i in y / 16 + 1..r0 {
                img[coordinates(r0 - i, r0 - j)].0[3] = 0;
            }
        }

        // draw when moving to next pixel in x-direction
        if !skip_draw {
            draw(img, alpha, x / 16 - 1, y / 16);
            draw(img, alpha, y / 16, x / 16 - 1);
            alpha = 0;
        }

        for _ in 0..16 {
            skip_draw = false;

            if x >= y {
                break 'l;
            }

            alpha += y as u16 % 16 + 1;
            if p < 0 {
                x += 1;
                p += (2 * x + 2) as i32;
            } else {
                // draw when moving to next pixel in y-direction
                if y % 16 == 0 {
                    draw(img, alpha, x / 16, y / 16);
                    draw(img, alpha, y / 16, x / 16);
                    skip_draw = true;
                    alpha = (x + 1) as u16 % 16 * 16;
                }

                x += 1;
                p -= (2 * (y - x) + 2) as i32;
                y -= 1;
            }
        }
    }

    // one corner pixel left
    if x / 16 == y / 16 {
        // column under current position possibly not yet accounted
        if x == y {
            alpha += y as u16 % 16 + 1;
        }
        let s = y as u16 % 16 + 1;
        let alpha = 2 * alpha - s * s;
        draw(img, alpha, x / 16, y / 16);
    }

    // remove remaining square of content in the corner
    let range = y / 16 + 1..r0;
    for i in range.clone() {
        for j in range.clone() {
            img[coordinates(r0 - i, r0 - j)].0[3] = 0;
        }
    }
}
