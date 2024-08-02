document.addEventListener('DOMContentLoaded', function() {
  // Function to display saved answers in the Summary page
  function displaySummaryAnswers() {
    var answersContainer1 = document.getElementById('ans1');
    var answersContainer2 = document.getElementById('ans2');
    var answersContainer3 = document.getElementById('ans3');
    var answersContainer4 = document.getElementById('ans4');
    var answersContainer5 = document.getElementById('ans5');
 
    var storedAnswers = localStorage.getItem('answers');
    if (storedAnswers && answersContainer1 && answersContainer2 && answersContainer3 && answersContainer4 && answersContainer5) {
      var answers = JSON.parse(storedAnswers);
      answersContainer1.innerHTML = answers.answ1;
      answersContainer2.innerHTML = answers.answ2;
      answersContainer3.innerHTML = answers.answ3;
      answersContainer4.innerHTML = answers.answ4;
      answersContainer5.innerHTML = answers.answ5;
    }
  }




  // Call displaySummaryAnswers when the Summary page loads
  displaySummaryAnswers();
});




function saveAnswersG2PreOral() {
  saveAnswers();
  window.location.href = 'g2_pretest_summary.html';
}




// Function to save answers to localStorage
function saveAnswers() {
  var answers = {
    answ1: document.getElementById('ans1').value,
    answ2: document.getElementById('ans2').value,
    answ3: document.getElementById('ans3').value,
    answ4: document.getElementById('ans4').value,
    answ5: document.getElementById('ans5').value,
  };
  localStorage.setItem('answers', JSON.stringify(answers));
}




// Function to save a copy of the answers
function saveCopy() {
  var storedAnswers = localStorage.getItem('answers');




  if (storedAnswers) {
    var answers = JSON.parse(storedAnswers);
    var blob = new Blob([JSON.stringify(answers)], { type: 'application/json' });




    // Create a temporary anchor element to trigger the download
    var a = document.createElement('a');
    var url = window.URL.createObjectURL(blob);
    a.href = url;
    a.download = 'combined_answers.json';
    document.body.appendChild(a);
    a.click();




    // Clean up
    window.URL.revokeObjectURL(url);
  }
}


  function startSpeechToText(inputId, btnId) {
    const inputField = document.getElementById(inputId);
    const micButton = document.getElementById(btnId); // Get the specific microphone button
 
    // Toggle the active class for the specific microphone button
    micButton.classList.toggle('active-mic');
 
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const recognition = 'webkitSpeechRecognition' in window ? new webkitSpeechRecognition() : new SpeechRecognition();
 
      recognition.lang = 'en-US';
      recognition.continuous = false;
      recognition.interimResults = false;
 
      recognition.onresult = function(event) {
        const result = event.results[0][0].transcript;
        inputField.value = result; // Set the value property for input fields
      };
 
      recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
      };
 
      recognition.onend = function() {
        micButton.classList.remove('active-mic');
      };
 
      recognition.start();
    } else {
      console.error('Speech recognition not supported.');
    }
  }
 
 
  //------------------------------ To Analyze -------------------//
  // Function to send answers for analysis
function analyzeAnswers() {
  var answers = {
      "answ1": document.getElementById('ans1').textContent.trim(),
      "answ2": document.getElementById('ans2').textContent.trim(),
      "answ3": document.getElementById('ans3').textContent.trim(),
      "answ4": document.getElementById('ans4').textContent.trim(),
      "answ5": document.getElementById('ans5').textContent.trim(),
      "grade_level": document.getElementById('gradeLevel').value.trim()
  };


  console.log('Sending answers:', answers);


  var csrftoken = getCookie('csrftoken');


  $.ajax({
      url: '/analyze_similarity/',
      type: 'POST',
      data: answers,
      dataType: 'json',
      headers: {
          'X-CSRFToken': csrftoken
      },
      success: function(response) {
          console.log('Received response:', response);
          displayResults(response);
          saveToLocalStorage(response);
          enableDoneButton();
      },
      error: function(xhr, status, error) {
          console.error('Error:', error);
          console.error('Status:', status);
          console.error('XHR:', xhr);
          // Handle error feedback if needed
      },
      complete: function() {
          document.getElementById("analyzeBtn").disabled = false; // Re-enable the button after analysis
      }
  });
}


// Ensure getCookie function exists to get the CSRF token
function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}


// Event listener for the "Analyze Answers" button
document.getElementById("analyzeBtn").addEventListener("click", function() {
  this.disabled = true; // Disable the "Analyze Answers" button during analysis
  analyzeAnswers();
});




function enableDoneButton() {
  var doneButton = document.getElementById('doneBtn');
  doneButton.disabled = false;
}


function displayResults(results) {
var resultContainers = {
    "answ1": document.getElementById('result-ans1'),
    "answ2": document.getElementById('result-ans2'),
    "answ3": document.getElementById('result-ans3'),
    "answ4": document.getElementById('result-ans4'),
    "answ5": document.getElementById('result-ans5')
};


for (var key in resultContainers) {
    if (results['results'][key]) {
        resultContainers[key].innerHTML = createResultHtml(results['results'][key]);
    } else {
        resultContainers[key].innerHTML = '<p>No data available</p>';
    }
}


var overallScoresContainer = document.getElementById('overallScoresContainer');


// Display overall scores
if (results.correct_answers && results.correct_answers.overall) {
  var overallTotalCount = results.correct_answers.overall.total_count;
  overallScoresContainer.innerHTML = `
      <div class="overall-scores">
          <p class="total-summary-scores">Total Scores: ${overallTotalCount}</p>
      </div>
  `;
} else {
  overallScoresContainer.innerHTML = '<p>No overall scores available</p>';
}
}


// Rest of your JavaScript code remains unchanged


function createResultHtml(resultData) {
  var resultDiv = document.createElement('div');
  resultDiv.classList.add('result-item');


  var correctness = resultData.result === 'Correct' ? 'green' : 'red';
  resultDiv.innerHTML = `
      <p class="result-expected-answer"><strong>Expected Answer:</strong> ${resultData.expected_answer}</p>
      <p class="result-status" style="color: ${correctness};"><strong>Result:</strong> ${resultData.result}</p>
  `;
  return resultDiv.outerHTML;
}


function saveAndRedirect1() {
  window.location.href = 'g2_pretest_overall.html';




}
function saveAndRedirect2() {
  window.location.href = 'g2_posttest_overall.html';




}

// Function to save data to localStorage
function saveToLocalStorage(response) {
  console.log("Saving response to local storage:", response); // Debug print



  if (response.correct_answers && response.correct_answers.overall && response.correct_answers.overall.total_count !== undefined) {
      localStorage.setItem('overallScores', response.correct_answers.overall.total_count);
      console.log("overallScores saved:", response.correct_answers.overall.total_count); // Debug print
  } else {
      localStorage.setItem('overallScores', 'N/A');
      console.log("overallScores saved:", 'N/A'); // Debug print
  }
 
  // Store literal scores
  if (response.correct_answers && response.correct_answers.literal && response.correct_answers.literal.total_count !== undefined) {
      localStorage.setItem('literalScores', response.correct_answers.literal.total_count);
      console.log("literalScores saved:", response.correct_answers.literal.total_count); // Debug print
  } else {
      localStorage.setItem('literalScores', 'N/A');
      console.log("literalScores saved:", 'N/A'); // Debug print
  }


  // Store inferential scores
  if (response.correct_answers && response.correct_answers.inferential && response.correct_answers.inferential.total_count !== undefined) {
      localStorage.setItem('inferentialScores', response.correct_answers.inferential.total_count);
      console.log("inferentialScores saved:", response.correct_answers.inferential.total_count); // Debug print
  } else {
      localStorage.setItem('inferentialScores', 'N/A');
      console.log("inferentialScores saved:", 'N/A'); // Debug print
  }


  // Store applied scores
  if (response.correct_answers && response.correct_answers.applied && response.correct_answers.applied.total_count !== undefined) {
      localStorage.setItem('appliedScores', response.correct_answers.applied.total_count);
      console.log("appliedScores saved:", response.correct_answers.applied.total_count); // Debug print
  } else {
      localStorage.setItem('appliedScores', 'N/A');
      console.log("appliedScores saved:", 'N/A'); // Debug print
  }


  // Store predicted reading level
  localStorage.setItem('readingLevel', response.predicted_comprehension_level ? response.predicted_comprehension_level : 'N/A');
  console.log("readingLevel saved:", response.predicted_comprehension_level ? response.predicted_comprehension_level : 'N/A'); // Debug print


  // Store literal feedback
  localStorage.setItem('literalFeedback', response.feedback && response.feedback.literal ? response.feedback.literal : 'No literal feedback available');
  console.log("literalFeedback saved:", response.feedback && response.feedback.literal ? response.feedback.literal : 'No literal feedback available'); // Debug print


  // Store inferential feedback
  localStorage.setItem('inferentialFeedback', response.feedback && response.feedback.inferential ? response.feedback.inferential : 'No inferential feedback available');
  console.log("inferentialFeedback saved:", response.feedback && response.feedback.inferential ? response.feedback.inferential : 'No inferential feedback available'); // Debug print


  // Store applied feedback
  localStorage.setItem('appliedFeedback', response.feedback && response.feedback.applied ? response.feedback.applied : 'No applied feedback available');
  console.log("appliedFeedback saved:", response.feedback && response.feedback.applied ? response.feedback.applied : 'No applied feedback available'); // Debug print


  // Store level feedback
  localStorage.setItem('levelFeedback', response.feedback && response.feedback.level ? response.feedback.level : 'No level feedback available');
  console.log("levelFeedback saved:", response.feedback && response.feedback.level ? response.feedback.level : 'No level feedback available'); // Debug print
}

