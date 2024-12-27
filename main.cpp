#include <tgbot/tgbot.h>
#include <iostream>
#include <fstream>
#include <unordered_set>
#include <unordered_map>
#include <string>
#include <cstdlib>      // for std::getenv
#include <cmath>        // for float calculations
#include <sstream>

// Constants from your code:
static const int64_t SPECIAL_USER_ID     = 77655677655;  // Replace with your special user ID
static const int64_t AUTHORIZED_USER_ID  = 6177929931;   // The "admin" user ID
static const char*   MUTED_USERS_FILE    = "muted_users.json";
static const char*   USERS_FILE         = "users.json";

// We'll store sets of user IDs for muted & known users
static std::unordered_set<int64_t> mutedUsers;
static std::unordered_set<int64_t> knownUsers;

// A per-user “conversation state” can be tracked in a map: user_id -> state
struct UserSession {
    std::string stage;
    double blokMateria = 0.0;
    double blokTotal   = 0.0;
};

static std::unordered_map<int64_t, UserSession> userSessions;

/**
 * Naive function to load an array of IDs from a file.
 * Expects the file to look like: [123, 456, 789]
 */
std::unordered_set<int64_t> loadIdsFromFile(const std::string& filename) {
    std::unordered_set<int64_t> result;
    std::ifstream infile(filename);
    if (!infile.is_open()) {
        return result;
    }
    std::stringstream buffer;
    buffer << infile.rdbuf();
    infile.close();
    std::string data = buffer.str();

    // Basic sanity check
    if (data.size() < 2 || data[0] != '[' || data[data.size() - 1] != ']') {
        return result;
    }
    // Strip the leading '[' and trailing ']'
    data.erase(data.begin());
    data.pop_back();

    // Split on commas
    std::stringstream ss(data);
    while (ss.good()) {
        std::string part;
        getline(ss, part, ',');
        // Trim
        if (!part.empty()) {
            // remove leading/trailing spaces
            while (!part.empty() && isspace(part.front())) {
                part.erase(part.begin());
            }
            while (!part.empty() && isspace(part.back())) {
                part.pop_back();
            }
            if (!part.empty()) {
                try {
                    int64_t val = std::stoll(part);
                    result.insert(val);
                } catch (...) {
                    // ignore parse error
                }
            }
        }
    }
    return result;
}

/**
 * Naive function to write an array of IDs to a file in [1, 2, 3] format.
 */
void saveIdsToFile(const std::unordered_set<int64_t>& ids, const std::string& filename) {
    std::ofstream outfile(filename, std::ios::trunc);
    if (!outfile.is_open()) {
        std::cerr << "Failed to open file for saving: " << filename << std::endl;
        return;
    }
    outfile << "[";
    bool first = true;
    for (auto& id : ids) {
        if (!first) {
            outfile << ", ";
        }
        outfile << id;
        first = false;
    }
    outfile << "]";
    outfile.close();
}

int main() {
    // Load IDs from files
    mutedUsers = loadIdsFromFile(MUTED_USERS_FILE);
    knownUsers = loadIdsFromFile(USERS_FILE);

    // Read BOT_TOKEN from environment variable
    const char* token = std::getenv("BOT_TOKEN");
    if (!token) {
        std::cerr << "Error: BOT_TOKEN environment variable not set." << std::endl;
        return 1;
    }

    try {
        TgBot::Bot bot(token);

        // /start command
        bot.getEvents().onCommand("start", [&](TgBot::Message::Ptr message) {
            int64_t userId = message->from->id;
            // If new user, add to knownUsers
            if (knownUsers.find(userId) == knownUsers.end()) {
                knownUsers.insert(userId);
                saveIdsToFile(knownUsers, USERS_FILE);
            }
            // Check if muted
            if (mutedUsers.find(userId) != mutedUsers.end()) {
                bot.getApi().sendMessage(userId, "⚠️ لقد تم كتمك من استخدام هذا البوت.");
                return;
            }

            // Personalized vs default welcome
            std::string welcome;
            if (userId == SPECIAL_USER_ID) {
                welcome = "اهلا زهراء في البوت مالتي 🌹\nاتمنى تستفادين منه ^^";
            } else {
                welcome = 
                    "السلام عليكم\n"
                    "البوت تم تطويرة بواسطة @iwanna2die حتى يساعد الطلاب ^^\n\n"
                    "اهلا وسهلا!";
            }

            bot.getApi().sendMessage(userId, welcome);

            // Show main menu (custom keyboard)
            TgBot::ReplyKeyboardMarkup::Ptr kb(new TgBot::ReplyKeyboardMarkup);
            kb->resizeKeyboard = true;
            kb->oneTimeKeyboard = true;

            // First row
            {
                TgBot::KeyboardButton::Ptr btn1(new TgBot::KeyboardButton);
                btn1->text = "حساب غياب النظري";
                TgBot::KeyboardButton::Ptr btn2(new TgBot::KeyboardButton);
                btn2->text = "حساب غياب العملي";
                kb->keyboard.push_back({btn1, btn2});
            }
            // Second row
            {
                TgBot::KeyboardButton::Ptr btn3(new TgBot::KeyboardButton);
                btn3->text = "ارسل رسالة لصاحب البوت";
                TgBot::KeyboardButton::Ptr btn4(new TgBot::KeyboardButton);
                btn4->text = "حساب درجتك بلبلوك";
                kb->keyboard.push_back({btn3, btn4});
            }

            bot.getApi().sendMessage(userId, 
                "اختر من القائمة:",
                false, 0, kb);
        });

        // Handle text messages (not commands)
        bot.getEvents().onAnyMessage([&](TgBot::Message::Ptr message) {
            // If it's a command, let the command handler do its job.
            if (!message->text.empty() && message->text[0] == '/') {
                return;
            }
            int64_t userId = message->from->id;
            if (mutedUsers.find(userId) != mutedUsers.end()) {
                // user is muted
                bot.getApi().sendMessage(userId, "⚠️ أنت مكتوم.");
                return;
            }
            auto& session = userSessions[userId];
            std::string text = message->text;

            // If user has no "stage", interpret as a menu choice.
            if (session.stage.empty()) {
                if (text == "حساب غياب النظري") {
                    session.stage = "GET_THEORETICAL_CREDIT";
                    bot.getApi().sendMessage(userId,
                        "اكتب رقم الكردت لمادة النظري (مثال: 3.0).\n\n"
                        "اكتب 'العودة للقائمة الرئيسية' للعودة.");
                } 
                else if (text == "حساب غياب العملي") {
                    session.stage = "GET_PRACTICAL_CREDIT";
                    bot.getApi().sendMessage(userId,
                        "اكتب رقم الكردت لمادة العملي (مثال: 1.5).\n\n"
                        "اكتب 'العودة للقائمة الرئيسية' للعودة.");
                } 
                else if (text == "ارسل رسالة لصاحب البوت") {
                    session.stage = "SEND_MESSAGE";
                    bot.getApi().sendMessage(userId,
                        "يمكنك إرسال رسالتك الآن، أو اكتب 'العودة للقائمة الرئيسية':");
                } 
                else if (text == "حساب درجتك بلبلوك") {
                    session.stage = "BLOK_MATERIA";
                    bot.getApi().sendMessage(userId, 
                        "شكد المادة عليها بلبلوك؟ (اكتب رقم فقط)\n"
                        "اكتب 'العودة للقائمة الرئيسية' للعودة.");
                } 
                else {
                    bot.getApi().sendMessage(userId,
                        "خيار غير معروف!\nاستخدم /start للبدء من جديد.");
                }
                return;
            }

            // The user is in a conversation stage
            if (session.stage == "GET_THEORETICAL_CREDIT") {
                if (text == "العودة للقائمة الرئيسية") {
                    session.stage.clear();
                    bot.getApi().sendMessage(userId, "تم الرجوع للقائمة الرئيسية. اكتب /start للعرض.");
                    return;
                }
                try {
                    double credit = std::stod(text);
                    double result = credit * 8.0 * 0.23;  // from your python code
                    std::ostringstream oss;
                    oss << "غيابك للنظري هو: " << result;
                    bot.getApi().sendMessage(userId, oss.str());
                } catch (...) {
                    bot.getApi().sendMessage(userId,
                        "الرجاء إدخال رقم فقط.\nمثال: 3.0 أو 2.5\n"
                        "اكتب 'العودة للقائمة الرئيسية' للعودة.");
                    return;
                }
                session.stage.clear();
            }
            else if (session.stage == "GET_PRACTICAL_CREDIT") {
                if (text == "العودة للقائمة الرئيسية") {
                    session.stage.clear();
                    bot.getApi().sendMessage(userId, "تم الرجوع للقائمة الرئيسية. اكتب /start للعرض.");
                    return;
                }
                try {
                    double credit = std::stod(text);
                    double result = credit * 8.0 * 0.1176470588;
                    std::ostringstream oss;
                    oss << "غيابك للعملي هو: " << result;
                    bot.getApi().sendMessage(userId, oss.str());
                } catch (...) {
                    bot.getApi().sendMessage(userId,
                        "الرجاء إدخال رقم فقط.\nمثال: 1 أو 1.5\n"
                        "اكتب 'العودة للقائمة الرئيسية'.");
                    return;
                }
                session.stage.clear();
            }
            else if (session.stage == "SEND_MESSAGE") {
                if (text == "العودة للقائمة الرئيسية") {
                    session.stage.clear();
                    bot.getApi().sendMessage(userId, "تم الرجوع للقائمة الرئيسية. اكتب /start للعرض.");
                    return;
                }
                // Forward to authorized user
                try {
                    std::string username = (!message->from->username.empty()) 
                        ? ("@" + message->from->username) 
                        : ("ID " + std::to_string(userId));
                    std::ostringstream oss;
                    oss << "رسالة من " << username << " (ID: " << userId << "):\n\n"
                        << text;
                    bot.getApi().sendMessage(AUTHORIZED_USER_ID, oss.str());
                    bot.getApi().sendMessage(userId, "تم إرسال الرسالة بنجاح.");
                } catch (...) {
                    bot.getApi().sendMessage(userId, "حصل خطأ أثناء إرسال الرسالة.");
                }
                session.stage.clear();
            }
            else if (session.stage == "BLOK_MATERIA") {
                if (text == "العودة للقائمة الرئيسية") {
                    session.stage.clear();
                    bot.getApi().sendMessage(userId, "تم الرجوع للقائمة الرئيسية. اكتب /start للعرض.");
                    return;
                }
                try {
                    session.blokMateria = std::stod(text);
                    session.stage = "BLOK_TOTAL";
                    bot.getApi().sendMessage(userId,
                        "شكد الدرجة الكلية لهذي المادة؟ (اكتب رقم فقط)\n"
                        "اكتب 'العودة للقائمة الرئيسية' للعودة.");
                } catch (...) {
                    bot.getApi().sendMessage(userId, "الرجاء إدخال رقم صالح.");
                }
            }
            else if (session.stage == "BLOK_TOTAL") {
                if (text == "العودة للقائمة الرئيسية") {
                    session.stage.clear();
                    bot.getApi().sendMessage(userId, "تم الرجوع للقائمة الرئيسية. اكتب /start للعرض.");
                    return;
                }
                try {
                    session.blokTotal = std::stod(text);
                    session.stage = "BLOK_TAKEN";
                    bot.getApi().sendMessage(userId,
                        "شكد خذيت؟ (اكتب رقم فقط)\n"
                        "اكتب 'العودة للقائمة الرئيسية' للعودة.");
                } catch (...) {
                    bot.getApi().sendMessage(userId, "الرجاء إدخال رقم صالح.");
                }
            }
            else if (session.stage == "BLOK_TAKEN") {
                if (text == "العودة للقائمة الرئيسية") {
                    session.stage.clear();
                    bot.getApi().sendMessage(userId, "تم الرجوع للقائمة الرئيسية. اكتب /start للعرض.");
                    return;
                }
                try {
                    double blokTakenValue = std::stod(text);
                    double blokMateriaVal = session.blokMateria;
                    double blokTotalVal   = session.blokTotal;
                    if (std::fabs(blokTotalVal) < 1e-9) {
                        blokTotalVal = 1.0;
                    }
                    double result = (blokMateriaVal * blokTakenValue) / blokTotalVal;
                    std::ostringstream oss;
                    oss << "درجتك بلبلوك هي: " << result;
                    bot.getApi().sendMessage(userId, oss.str());
                } catch (...) {
                    bot.getApi().sendMessage(userId, "الرجاء إدخال رقم صالح.");
                    return;
                }
                session.stage.clear();
            }
            else {
                bot.getApi().sendMessage(userId,
                    "لم أفهم رسالتك. استخدم /start للبدء من جديد.");
            }
        });

        // /muteid <userid>
        bot.getEvents().onCommand("muteid", [&](TgBot::Message::Ptr message) {
            int64_t userId = message->from->id;
            if (userId != AUTHORIZED_USER_ID) {
                bot.getApi().sendMessage(userId, "You are not authorized.");
                return;
            }
            auto parts = TgBot::Utils::split(message->text, ' ');
            if (parts.size() != 2) {
                bot.getApi().sendMessage(userId, "Usage: /muteid <userid>");
                return;
            }
            try {
                int64_t targetId = std::stoll(parts[1]);
                if (mutedUsers.find(targetId) != mutedUsers.end()) {
                    bot.getApi().sendMessage(userId, "User is already muted.");
                } else {
                    mutedUsers.insert(targetId);
                    saveIdsToFile(mutedUsers, MUTED_USERS_FILE);
                    bot.getApi().sendMessage(userId, "User muted successfully.");
                }
            } catch (...) {
                bot.getApi().sendMessage(userId, "Provide a valid user ID.");
            }
        });

        // /unmuteid <userid>
        bot.getEvents().onCommand("unmuteid", [&](TgBot::Message::Ptr message) {
            int64_t userId = message->from->id;
            if (userId != AUTHORIZED_USER_ID) {
                bot.getApi().sendMessage(userId, "You are not authorized.");
                return;
            }
            auto parts = TgBot::Utils::split(message->text, ' ');
            if (parts.size() != 2) {
                bot.getApi().sendMessage(userId, "Usage: /unmuteid <userid>");
                return;
            }
            try {
                int64_t targetId = std::stoll(parts[1]);
                if (mutedUsers.find(targetId) == mutedUsers.end()) {
                    bot.getApi().sendMessage(userId, "User is not muted.");
                } else {
                    mutedUsers.erase(targetId);
                    saveIdsToFile(mutedUsers, MUTED_USERS_FILE);
                    bot.getApi().sendMessage(userId, "User unmuted successfully.");
                }
            } catch (...) {
                bot.getApi().sendMessage(userId, "Provide a valid user ID.");
            }
        });

        // /mutelist
        bot.getEvents().onCommand("mutelist", [&](TgBot::Message::Ptr message) {
            int64_t userId = message->from->id;
            if (userId != AUTHORIZED_USER_ID) {
                bot.getApi().sendMessage(userId, "You are not authorized.");
                return;
            }
            if (mutedUsers.empty()) {
                bot.getApi().sendMessage(userId, "No muted users.");
            } else {
                std::ostringstream oss;
                oss << "Muted users:\n";
                for (auto& id : mutedUsers) {
                    oss << id << "\n";
                }
                bot.getApi().sendMessage(userId, oss.str());
            }
        });

        // /new <message> (broadcast)
        bot.getEvents().onCommand("new", [&](TgBot::Message::Ptr message) {
            int64_t userId = message->from->id;
            if (userId != AUTHORIZED_USER_ID) {
                bot.getApi().sendMessage(userId, "You are not authorized.");
                return;
            }
            auto parts = TgBot::Utils::split(message->text, ' ');
            if (parts.size() <= 1) {
                bot.getApi().sendMessage(userId, "Usage: /new <message>");
                return;
            }
            // Rebuild the broadcast message (skipping /new)
            std::string broadcastMsg;
            for (size_t i = 1; i < parts.size(); ++i) {
                broadcastMsg += parts[i] + " ";
            }
            int sentCount = 0;
            for (auto uid : knownUsers) {
                try {
                    bot.getApi().sendMessage(uid, broadcastMsg);
                    sentCount++;
                } catch (...) {
                    // Could not send to this user
                }
            }
            std::ostringstream oss;
            oss << "تم إرسال الرسالة إلى " << sentCount << " مستخدم.";
            bot.getApi().sendMessage(userId, oss.str());
        });

        // /user_id <message> => Send to SPECIAL_USER_ID
        bot.getEvents().onCommand("user_id", [&](TgBot::Message::Ptr message) {
            int64_t userId = message->from->id;
            if (userId != AUTHORIZED_USER_ID) {
                bot.getApi().sendMessage(userId, "You are not authorized.");
                return;
            }
            auto parts = TgBot::Utils::split(message->text, ' ');
            if (parts.size() <= 1) {
                bot.getApi().sendMessage(userId, "Usage: /user_id <message>");
                return;
            }
            std::string userMsg;
            for (size_t i = 1; i < parts.size(); ++i) {
                userMsg += parts[i] + " ";
            }
            try {
                std::ostringstream oss;
                oss << "Message from " 
                    << (message->from->username.empty() 
                        ? std::to_string(userId) 
                        : message->from->username)
                    << " (ID: " << userId << "):\n" 
                    << userMsg;
                bot.getApi().sendMessage(SPECIAL_USER_ID, oss.str());
                bot.getApi().sendMessage(userId, "تم إرسال رسالتك بنجاح!");
            } catch (...) {
                bot.getApi().sendMessage(userId, "حصل خطأ أثناء إرسال الرسالة.");
            }
        });

        // Start polling
        TgBot::TgLongPoll longPoll(bot);
        std::cout << "Bot started polling..." << std::endl;
        while (true) {
            longPoll.start();
        }
    } catch (std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
