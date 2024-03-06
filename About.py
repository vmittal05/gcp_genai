import streamlit as st

st.set_page_config(
    page_title="Asian Paints" ,
    page_icon="👨‍🎨",
)

left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image('logo-color.png')

st.divider()

st.markdown('''
            Welcome to Beautiful Homes - Your ultimate destination for top-notch interior design services. Our panel of experienced interior designers specializes in crafting stunning and functional spaces for bedrooms, bathrooms, kitchens, and living rooms. We believe that your home's interior design should be a true reflection of your personality and style. With our personalized service, you can expect tailor-made designs that suit your preferences. From conceptualization to execution, we provide end-to-end services, ensuring a seamless experience for you.
            
            Here are some of the things that Asian Paints offers:
           
            • **Paints and coatings**: We offer a wide range of paints and coatings for both interior and exterior use. Our paints are available in a variety of colors and finishes, so you can find the perfect look for your home.
            
            • **Wallpapers**: We offer a wide range of wallpapers from traditional to modern designs. Our wallpapers are made from high-quality materials, so they will last for years to come.
            
            • **Furniture**: We offer a wide range of furniture for every room in your home. Our furniture is made from high-quality materials and is designed to last.
            
            • **Accessories**: We offer a wide range of accessories to help you complete the look of your home. Our accessories include everything from curtains and blinds to rugs and cushions.
            
            
            If you are looking for a way to create your dream home, Asian Paints is the perfect choice. We offer a wide range of products and services to help you make your house a beautiful home.
            ''')
