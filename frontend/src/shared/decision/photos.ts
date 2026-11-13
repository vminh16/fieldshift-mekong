/** Crop photos in /public/crops (Wikimedia Commons, cropped + resized). Full credits: public/crops/CREDITS.md */
export interface CropPhoto { src: string; author: string; license: string; page: string }

export const CROP_PHOTO: Record<string, CropPhoto> = {
  rice: { src: '/crops/rice.jpg', author: "Dragfyre", license: "CC BY-SA 3.0", page: "https://commons.wikimedia.org/wiki/File:Rice_fields_in_Can_Tho_01.JPG" },
  mungbean: { src: '/crops/mungbean.jpg', author: "Shanmugamp7", license: "CC BY-SA 3.0", page: "https://commons.wikimedia.org/wiki/File:Mung_bean_field.jpg" },
  soybean: { src: '/crops/soybean.jpg', author: "United Soybean Board", license: "CC BY 2.0", page: "https://commons.wikimedia.org/wiki/File:Soybean_Plants_in_the_Field_(9624015808).jpg" },
  peanut: { src: '/crops/peanut.jpg', author: "Alabama Extension", license: "CC0", page: "https://commons.wikimedia.org/wiki/File:Field_of_Peanut_Plants.jpg" },
  fallow_cover: { src: '/crops/fallow_cover.jpg', author: "Hugh Venables", license: "CC BY-SA 2.0", page: "https://commons.wikimedia.org/wiki/File:Cover_crop_in_field_-_geograph.org.uk_-_5236028.jpg" },
}
