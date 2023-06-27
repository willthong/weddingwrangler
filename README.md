# Wedding Wrangle

A Django project to help you wrangle a wedding's guests. Wedding Wrangle will:

* Import a CSV of guests and the following data:
    * Title
    * First name
    * Surname
    * Email
    * Dietaries
* Allow users (wedding organisers) to log in and see a dashboard of their guests, as
  well as update each guest's details and partnerships (one-to-one relationship with
  another guest)
* Send emails to guests asking them to RSVP using a random string-encoded URL 
    * Guests' partners are emailed at the same time, with both links for convenience
* Serve random string-encoded URLs to allow guests to mark boolean attendance and
  complex dietary requirements (many-to-many)
    * As a stretch, it could also allow guests to upload an image to the database for
      later use in some sort of collage or slideshow
* Support CSV export of guestlist
    * This will allow for mail-merging of physical invites and placecards
* Support export of QR codes as an alternative RSVP option

The project will mostly store and return text. It will accept and return images too, for
'memory' photos from guests, and as QR codes. Logged-in users will have the ability to
interactively edit guest details.

