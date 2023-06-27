# Wedding Wrangle

A Django project to help you wrangle a wedding's guests. Wedding Wrangle will:

* Import a CSV of guests and the following data:
    * First name
    * Surname
    * Email
    * Dietaries
* Allow users (wedding organisers) to log in and see a dashboard of their guests, as
  well as update each guest's details and partnerships (one-to-one relationship with
  another guest)
* Send emails to guests asking them to RSVP using a random string-encoded URL 
    * Guests' partners are emailed at the same time
* Serve random string-encoded URLs to allow guests to mark boolean attendance and
  complex dietary requirements (many-to-many)
    * As a stretch, it could also allow guests to upload an image to the database for
      later use in some sort of collage or slideshow
* Support CSV export of guestlist

The project will mostly store and return text. Logged-in users will have the ability to
interactively edit guest details.
